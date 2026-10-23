// TODO: APNG support? Requires FFmpeg, apparently.

#include <assert.h>
#include <inttypes.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <linux/seccomp.h>
#include <sys/prctl.h>
#include <sys/syscall.h>

#include <lcms2.h>
#include <MagickWand/MagickWand.h>

#include "worker-sandbox.h"

#ifndef unreachable
#define unreachable __builtin_unreachable
#endif

static ssize_t read_stdin(ssize_t capacity, unsigned char buf[capacity]) {
	ssize_t bytes_read = 0;

	while (bytes_read < capacity) {
		auto remaining = (size_t)(capacity - bytes_read);
		size_t r = fread(buf + bytes_read, sizeof(char), remaining, stdin);
		bytes_read += (ssize_t)r;

		if (r < remaining) {
			if (ferror(stdin)) {
				perror("Failed to read stdin");
				return -1;
			}
			assert(feof(stdin));
			return bytes_read;
		}
	}

	fprintf(stderr, "Input hit limit of %zd bytes\n", capacity);
	return -1;
}

static void log_wand_exception(MagickWand* wand) {
	ExceptionType severity;
	auto description = MagickGetException(wand, &severity);
	(void)severity;
	(void)fprintf(stderr, "MagickWand exception: %s\n", description);
	MagickRelinquishMemory(description);
}

struct crop_source {
	int16_t x;
	int16_t y;
	int16_t width;
	int16_t height;
};

struct operation {
	enum {
		OP_INVALID,
		OP_COVER,
		OP_THUMBNAIL,
		OP_AVATAR,
		OP_AVATAR_SOURCE,
		OP_BANNER,
	} type;
	struct crop_source crop;
};

static bool is_empty_crop(struct crop_source crop) [[unsequenced]] {
	return (
		   crop.x      == 0
		&& crop.y      == 0
		&& crop.width  == 0
		&& crop.height == 0
	);
}

/** Returns `value` scaled by m/d < 1 and rounded. */
static int16_t scale(int16_t value, int16_t m, int16_t d)
#ifdef NDEBUG
	[[unsequenced]]
#endif
{
	assert(value >= 0 && m >= 0 && d > 0 && m < d);
	return (int16_t)(((int_least32_t)value * m + d / 2) / d);
}

constexpr int16_t THUMBNAIL_HEIGHT = 250;

#define MAX(a, b) ((a) > (b) ? (a) : (b))

static struct crop_source autocrop_thumbnail(int16_t image_width, int16_t image_height) {
	{
		int16_t max_width = (int16_t)(2 * MAX(image_height, THUMBNAIL_HEIGHT));
		if (image_width > max_width)
			// crop to 2:1 aspect ratio evenly
			return (struct crop_source){
				.x = (int16_t)((image_width - max_width) / 2),
				.y = 0,
				.width = max_width,
				.height = image_height,
			};
	}

	{
		int16_t max_height = MAX((int16_t)(2 * image_width), THUMBNAIL_HEIGHT);
		if (image_height > max_height)
			// crop to 1:2 aspect ratio anchored to top
			return (struct crop_source){
				.x = 0,
				.y = 0,
				.width = image_width,
				.height = max_height,
			};
	}

	// no crop
	return (struct crop_source){
		.x = 0,
		.y = 0,
		.width = 0,
		.height = 0,
	};
}

/** The maximum number of pixels supported in either dimension, matching WebP. */
constexpr int16_t DIM_MAX = 0x3fff;

#define CHECK(expr) do { if ((expr) == MagickFalse) goto exception; } while (0)

static void NOFAIL(MagickBooleanType result) {
	assert(result != MagickFalse);
}

static int sandboxed_main(struct operation const op) {
	auto wand = NewMagickWand();  // `_exit`s on allocation failure

	// Read the image from stdin.
	// `MagickReadImageFile(wand, stdin)` buffers to a file when stdin isn't seekable.
	{
		ssize_t max_size = 50L * 1024 * 1024 + 1;
		unsigned char* buf = malloc((size_t)max_size);
		if (buf == nullptr) {
			fputs("Failed to allocate memory for stdin\n", stderr);
			return EXIT_FAILURE;
		}

		ssize_t bytes_read = read_stdin(max_size, buf);
		if (bytes_read < 0) return EXIT_FAILURE;

		if (MagickReadImageBlob(wand, buf, (size_t)bytes_read) == MagickFalse) {
			#pragma GCC diagnostic push
			#pragma GCC diagnostic ignored "-Wswitch-enum"
			switch (MagickGetExceptionType(wand)) {
			case MissingDelegateError:
			case PolicyError:  // assume delegate blocked by policy
				(void)puts("error=unsupported-format");
				return EXIT_FAILURE;

			default:
				goto exception;
			}
			#pragma GCC diagnostic pop
		}

		free(buf);
	}

	bool deanimate = op.type == OP_THUMBNAIL;
	char const* original_format;

	{
		char* format = MagickGetImageFormat(wand);
		assert(format != nullptr);  // `AcquireString` exits on alloc failure
		if (strcmp(format, "WEBP") == 0) {
			original_format = "WEBP";
		} else if (strcmp(format, "PNG") == 0) {
			original_format = "PNG";

			// PNG coder sets `page` based on metadata, which is nonsense
			NOFAIL(MagickSetImagePage(wand, 0, 0, 0, 0));
		} else if (strcmp(format, "GIF") == 0) {
			original_format = "GIF";
		} else if (
			   strcmp(format, "JPEG") == 0
			|| strcmp(format, "UHDR") == 0
			|| strcmp(format, "MPO")  == 0
		) {
			original_format = "JPEG";

			// MPO is usually not intended as animation. Could read the MP Type metadata in the future if there's demand.
			deanimate = true;
		} else {
			// NOTE: It's not safe to get here. We rely on policy to disable most formats, which will fail at read time.
			(void)puts("error=unsupported-format");
			fprintf(stderr, "Unsupported format: '%s'\n", format);
			return EXIT_FAILURE;
		}
		MagickRelinquishMemory(format);
	}

	// TODO: Check pixel data in case someone uploaded an unoptimized PNG or WebP.
	// NOTE: `MagickGetImageAlphaChannel` can fail with an exception if the number of images is 0, which isn't a condition that can be distinguished by return value.
	bool has_alpha = MagickGetImageAlphaChannel(wand) != MagickFalse;

	size_t num_images = MagickGetNumberImages(wand);
	bool is_animated = num_images > 1;

	if (is_animated) {
		{
			// TODO: this is a waste of memory (two fully decompressed copies of all frames loaded at once), especially in the `deanimate` case, but `CoalesceImages` is just complicated enough that I didn't want to reimplement it right away
			auto coalesced = MagickCoalesceImages(wand);
			if (coalesced == nullptr) goto exception;

			DestroyMagickWand(wand);
			wand = coalesced;
		}

		if (deanimate) {
			NOFAIL(MagickNextImage(wand));
			for (size_t i = 0; i < num_images - 1; i++) {
				NOFAIL(MagickRemoveImage(wand));
			}
		}
	}

	MagickResetIterator(wand);
	while (MagickNextImage(wand) != MagickFalse) {
		CHECK(MagickAutoOrientImage(wand));
	}
	NOFAIL(MagickSetIteratorIndex(wand, 0));

	// NOTE: must be measured after coalescing, and after auto-orienting
	int16_t original_width, original_height;
	{
		size_t
			image_width_st = MagickGetImageWidth(wand),
			image_height_st = MagickGetImageHeight(wand);

		if (
			image_width_st > (size_t)DIM_MAX
			|| image_height_st > (size_t)DIM_MAX
		) {
			(void)puts("error=dimensions-over-limit");
			return EXIT_FAILURE;
		}

		original_width = (int16_t)image_width_st;
		original_height = (int16_t)image_height_st;
	}

	auto image_width  = original_width;
	auto image_height = original_height;

	if (op.type == OP_THUMBNAIL || op.type == OP_AVATAR) {
		auto crop = op.crop;

		if (is_empty_crop(crop) && op.type == OP_THUMBNAIL) {
			crop = autocrop_thumbnail(image_width, image_height);
		}

		if (
			   crop.x >= image_width
			|| crop.y >= image_height
			|| crop.x > INT16_MAX - crop.width
			|| crop.y > INT16_MAX - crop.height
			|| crop.x + crop.width  > image_width
			|| crop.y + crop.height > image_height
		) {
			fprintf(
				stderr,
				"Warning: skipping out-of-bounds crop (%d, %d, %d, %d) on %dx%d image\n",
				(int)crop.x, (int)crop.y, (int)crop.width, (int)crop.height,
				(int)image_width, (int)image_height
			);
		} else if (!is_empty_crop(crop) && (crop.width != image_width || crop.height != image_height)) {
			MagickResetIterator(wand);
			while (MagickNextImage(wand) != MagickFalse) {
				CHECK(MagickCropImage(wand, (size_t)crop.width, (size_t)crop.height, crop.x, crop.y));
				NOFAIL(MagickSetImagePage(wand, 0, 0, 0, 0));
			}

			image_width = crop.width;
			image_height = crop.height;
		}
	}

	int16_t max_width, max_height;

	switch (op.type) {
	case OP_THUMBNAIL:
		max_height = THUMBNAIL_HEIGHT;
		max_width = (int16_t)(2 * THUMBNAIL_HEIGHT);
		break;

	case OP_COVER:
		max_width = 1024;
		max_height = 3000;
		break;

	case OP_AVATAR:
		max_width = max_height = 100;
		break;

	case OP_AVATAR_SOURCE:
		max_width = 600;
		max_height = 500;
		break;

	case OP_BANNER:
		max_width = 1650;
		max_height = 250;
		break;

	case OP_INVALID:
	default:
		assert(false);
		unreachable();
	}

	auto resize_width  = image_width;
	auto resize_height = image_height;

	if (image_width > max_width) {
		resize_width = max_width;
		resize_height = scale(image_height, max_width, image_width);
	}

	if (resize_height > max_height) {
		resize_width = scale(image_width, max_height, image_height);
		resize_height = max_height;
	}

	if (resize_width == 0) resize_width = 1;
	if (resize_height == 0) resize_height = 1;

	if (resize_width != image_width || resize_height != image_height) {
		void* srgb_profile_bytes;
		cmsUInt32Number srgb_profile_len;
		{
			auto srgb_profile = cmsCreate_sRGBProfile();
			if (
				srgb_profile == nullptr
				|| !cmsSaveProfileToMem(srgb_profile, nullptr, &srgb_profile_len)
				|| (srgb_profile_bytes = malloc((size_t)srgb_profile_len)) == nullptr
				|| !cmsSaveProfileToMem(srgb_profile, srgb_profile_bytes, &srgb_profile_len)
			) {
				fputs("Failed to load sRGB profile\n", stderr);
				return EXIT_FAILURE;
			}
			(void)cmsCloseProfile(srgb_profile);
		}

		MagickResetIterator(wand);
		while (MagickNextImage(wand) != MagickFalse) {
			CHECK(MagickProfileImage(wand, "icc", srgb_profile_bytes, (size_t)srgb_profile_len));
			CHECK(MagickTransformImageColorspace(wand, RGBColorspace));
			CHECK(MagickResizeImage(wand, (size_t)resize_width, (size_t)resize_height, MagicKernelSharp2021Filter));
			CHECK(MagickTransformImageColorspace(wand, sRGBColorspace));  // TODO: wider gamut if input was?
			CHECK(MagickStripImage(wand));
		}

		free(srgb_profile_bytes);
	} else {  // no resize, needs stripping
		if (op.type == OP_THUMBNAIL || op.type == OP_AVATAR) {
			// thumbnails and avatars are always converted to sRGB and stripped
			MagickResetIterator(wand);
			while (MagickNextImage(wand) != MagickFalse) {
				CHECK(MagickTransformImageColorspace(wand, sRGBColorspace));
				// TODO: check tIME, oFFs, non-PNG EXIF
				CHECK(MagickStripImage(wand));
			}
		} else {
			MagickResetIterator(wand);
			while (MagickNextImage(wand) != MagickFalse) {
				// `MagickStripImage` minus colorspace
				CHECK(MagickProfileImage(wand, "!icc,!hdrgm,*", nullptr, 0));
				CHECK(MagickSetImageArtifact(wand, "png:exclude-chunk", "bKGD,caNv,eXIf,iTXt,pHYs,sRGB,tEXt,zCCP,zTXt,date"));

				(void)MagickDeleteImageProperty(wand, "comment");
				(void)MagickDeleteImageProperty(wand, "date:create");
				(void)MagickDeleteImageProperty(wand, "date:modify");
				(void)MagickDeleteImageProperty(wand, "date:timestamp");
			}
		}
	}

	// XXX: this might actually break WebP output if enabled?
	if (false /* GIF output */) {
		{
			auto optimized = MagickOptimizeImageLayers(wand);
			if (optimized == nullptr) goto exception;

			DestroyMagickWand(wand);
			wand = optimized;
		}

		NOFAIL(MagickOptimizeImageTransparency(wand));
	}

	NOFAIL(MagickSetIteratorIndex(wand, 0));

	// a value of n indicates scaling by 1/n or smaller
	enum {
		SCALE_1_1 = 1,
		SCALE_1_2 = 2,
		SCALE_1_4 = 4,
	} scale_bucket = (
		resize_height * 4 <= image_height ? 4 :
		resize_height * 2 <= image_height ? 2 : 1
	);

	{
		size_t quality = MagickGetImageCompressionQuality(wand);
		assert(quality <= 100);

		if (quality == 0) {
			quality = 92;  // JPEG default. WebP default is 75.
		} else {
			// Adjust quality settings relative to source to avoid lowering quality after scaling.
			// TODO: Test exact values, possibly pick different adjustments and max for WebP
			// TODO: quality scale mismatch between WebP source and JPEG destination or the reverse
			quality += (
				scale_bucket > 2 ? 5 :
				scale_bucket > 1 ? 3 : 0
			);
		}

		NOFAIL(MagickSetImageCompressionQuality(wand, quality < 92 ? quality : 92));
	}

	{
		char const* out_format;
		if (has_alpha || (is_animated && !deanimate) || ALWAYS_WEBP) {
			out_format = "WEBP";
			CHECK(MagickSetOption(wand, "webp:method", "6"));
			CHECK(MagickSetOption(wand, "webp:use-sharp-yuv", "true"));
		} else {
			out_format = "JPEG";

			if (scale_bucket > 1)
				(void)MagickDeleteImageProperty(wand, "jpeg:sampling-factor");
		}

		if (
			printf(
				"original_format=%s\n"
				"original_width=%" PRIi16 "\n"
				"original_height=%" PRIi16 "\n"
				"output_format=%s\n"
				"output_width=%" PRIi16 "\n"
				"output_height=%" PRIi16 "\n"
				"\n",
				original_format,
				original_width,
				original_height,
				out_format,
				resize_width,
				resize_height
			) < 0
		) {
			perror("Failed to write metadata");
			return EXIT_FAILURE;
		}

		CHECK(MagickSetImageFormat(wand, out_format));
		CHECK(MagickWriteImagesFile(wand, stdout));

		if (puts("\n--END--") < 0 || fflush(stdout) != 0) {
			perror("Failed to flush stdout");
			return EXIT_FAILURE;
		}
	}

#ifdef REDUNDANT_CLEANUP
	DestroyMagickWand(wand);
	MagickWandTerminus();
#endif

	return EXIT_SUCCESS;

exception:
	log_wand_exception(wand);
	return EXIT_FAILURE;
}

static bool c_isdigit(char c) [[unsequenced]] {
	return c >= '0' && c <= '9';
}

/** Parses strictly the default decimal representation (`printf %d`) of a non-negative coordinate, returning -1 on error. */
static int16_t parse_coord(char const* s) [[reproducible]] {
	enum { INT16_MAX_DIGITS = 5 };

	if (s[0] == '0' && s[1] == '\0') return 0;

	// invalid first digit, including empty string and leading zero
	if (s[0] < '1' || s[0] > '9') return -1;

	int_least32_t value = s[0] - '0';

	for (int i = 1; i < INT16_MAX_DIGITS; i++) {
		if (s[i] == '\0') return (int16_t)value;
		if (!c_isdigit(s[i])) return -1;
		value = value * 10 + (s[i] - '0');
	}

	// overflow
	if (s[INT16_MAX_DIGITS] != '\0' || value > INT16_MAX) return -1;

	return (int16_t)value;
}

/**
 * Parses command-line arguments into an operation, or one with type `OP_INVALID` on error.
 */
static struct operation parse_args(int argc, char const* const* argv) [[reproducible]] {
	static constexpr struct operation OP_INVALID_S = {.type = OP_INVALID};

	if (argc < 2) return OP_INVALID_S;

	char const* cmd = argv[1];

	if (strcmp(cmd, "cover") == 0) {
		if (argc != 2) return OP_INVALID_S;
		return (struct operation){.type = OP_COVER};
	}

	if (strcmp(cmd, "avatar-source") == 0) {
		if (argc != 2) return OP_INVALID_S;
		return (struct operation){.type = OP_AVATAR_SOURCE};
	}

	if (strcmp(cmd, "banner") == 0) {
		if (argc != 2) return OP_INVALID_S;
		return (struct operation){.type = OP_BANNER};
	}

	bool is_thumbnail_op;
	if (
		(is_thumbnail_op = strcmp(cmd, "thumbnail") == 0)
		|| strcmp(cmd, "avatar") == 0
	) {
		if (argc != 6) return OP_INVALID_S;

		struct crop_source crop = {
			.x      = parse_coord(argv[2]),
			.y      = parse_coord(argv[3]),
			.width  = parse_coord(argv[4]),
			.height = parse_coord(argv[5]),
		};

		return (
			   crop.x      >= 0
			&& crop.y      >= 0
			&& crop.width  >= 0
			&& crop.height >= 0
			&& (is_empty_crop(crop) || (crop.width != 0 && crop.height != 0))
		)
			? (struct operation){
				.type = is_thumbnail_op ? OP_THUMBNAIL : OP_AVATAR,
				.crop = crop,
			}
			: OP_INVALID_S;
	}

	return OP_INVALID_S;
}

int main() {
	if (prctl(PR_SET_NO_NEW_PRIVS, 1UL, 0UL, 0UL, 0UL) != 0) {
		perror("Failed to set no-new-privs");
		return EXIT_FAILURE;
	}

	MagickWandGenesis();

	if (!sandbox_enter()) {
		return EXIT_FAILURE;
	}

	static constexpr int ARGV_MAX = 6;
	char cmdline[sizeof "thumbnail 16384 16384 16384 16384\n"];
	if (fgets(cmdline, sizeof cmdline, stdin) == nullptr) {
		perror("Failed to read cmdline");
		return EXIT_FAILURE;
	}
	{
		char* end = strchr(cmdline, '\n');
		if (end == nullptr || end == cmdline) goto bad_cmdline;
		*end = '\0';
	}

	int argc = 1;
	char const* argv[ARGV_MAX];

	{
		char* arg = cmdline;
		char* arg_end;
		for (;;) {
			argv[argc++] = arg;
			arg_end = strchr(arg, ' ');

			if (arg_end == nullptr) break;

			*arg_end = '\0';
			arg = arg_end + 1;

			if (argc == ARGV_MAX) goto bad_cmdline;
		}
	}

	auto const op = parse_args(argc, argv);
	if (op.type == OP_INVALID) goto bad_cmdline;

	return sandboxed_main(op);

bad_cmdline:
	(void)puts("error=bad-cmdline");
	return EXIT_FAILURE;
}
