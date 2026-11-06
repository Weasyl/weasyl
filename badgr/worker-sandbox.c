#define _GNU_SOURCE

#include <errno.h>
#include <stdio.h>
#include <string.h>

#include <sched.h>
#include <sys/mman.h>

#include <seccomp.h>

#include "worker-sandbox.h"

#define CHECK(expr) \
	do { \
		int const check_r = (expr); \
		if (check_r < 0) { \
			fprintf(stderr, "libseccomp operation failed: %s\n", strerror(-check_r)); \
			return false; \
		} \
	} while (0)

#define LEN(arr) (sizeof (arr) / sizeof (arr)[0])

constexpr int ALWAYS_ALLOWED[] = {
	SCMP_SYS(brk),
	SCMP_SYS(close),
	SCMP_SYS(exit),
	SCMP_SYS(exit_group),
	SCMP_SYS(futex),
	SCMP_SYS(getpid),
	SCMP_SYS(gettid),
	SCMP_SYS(membarrier),
	SCMP_SYS(mremap),
	SCMP_SYS(munmap),
	SCMP_SYS(read),
	SCMP_SYS(readv),
	SCMP_SYS(rseq),
	SCMP_SYS(rt_sigprocmask),
	SCMP_SYS(write),
	SCMP_SYS(writev),
};

bool sandbox_enter() {
	auto ctx = seccomp_init(SCMP_ACT_ERRNO(EPERM));
	if (ctx == nullptr) {
		fputs("seccomp_init failed\n", stderr);
		return false;
	}

	CHECK(seccomp_attr_set(ctx, SCMP_FLTATR_CTL_TSYNC, 1));
	CHECK(seccomp_attr_set(ctx, SCMP_FLTATR_CTL_OPTIMIZE, 2));

	for (size_t i = 0; i < LEN(ALWAYS_ALLOWED); i++) {
		CHECK(seccomp_rule_add(ctx, SCMP_ACT_ALLOW, ALWAYS_ALLOWED[i], 0));
	}

	// `clone`
	// musl rev d64148a8743ad9ed0594091d2ff141b1e9334d4b src/thread/pthread_create.c:243
	// glibc checked against chromium rev fa3003fc748d75b7f55e9a3e9e815079928ae7a8 sandbox/linux/seccomp-bpf-helpers/syscall_parameters_restrictions.cc:151
	static constexpr int THREAD_FLAGS = (
		  CLONE_VM
		| CLONE_FS
		| CLONE_FILES
		| CLONE_SIGHAND
		| CLONE_THREAD
		| CLONE_SYSVSEM
		| CLONE_SETTLS
		| CLONE_PARENT_SETTID
		| CLONE_CHILD_CLEARTID
		// `CLONE_DETACHED` is musl only
	);
	CHECK(
		seccomp_rule_add(
			ctx, SCMP_ACT_ALLOW, SCMP_SYS(clone), 1,
			SCMP_A0_64(SCMP_CMP_MASKED_EQ, ~(uint64_t)CLONE_DETACHED, THREAD_FLAGS)
		)
	);

	// `madvise`, from chromium
	static constexpr int MADV_ALLOWED[] = {
		MADV_DONTNEED,
		MADV_WILLNEED,
		MADV_RANDOM,
		MADV_REMOVE,
		MADV_NORMAL,
		MADV_FREE,
	};
	for (size_t i = 0; i < LEN(MADV_ALLOWED); i++) {
		CHECK(
			seccomp_rule_add(
				ctx, SCMP_ACT_ALLOW, SCMP_SYS(madvise), 1,
				SCMP_A2_64(SCMP_CMP_EQ, (uint64_t)MADV_ALLOWED[i])
			)
		);
	}

	// `mmap`, flags derived from chromium
	static constexpr int MMAP_ALLOWED = (
		  MAP_SHARED
		| MAP_PRIVATE
		| MAP_ANONYMOUS
		| MAP_STACK
		| MAP_NORESERVE
		| MAP_LOCKED
		//| MAP_DROPPABLE  // not defined by musl
	);
	CHECK(
		seccomp_rule_add(
			ctx, SCMP_ACT_ALLOW, SCMP_SYS(mmap), 2,
			SCMP_A2_64(SCMP_CMP_MASKED_EQ, ~(uint64_t)(PROT_READ | PROT_WRITE), 0),
			SCMP_A3_64(SCMP_CMP_MASKED_EQ, ~(uint64_t)MMAP_ALLOWED, 0)
		)
	);

	// `mprotect`
	CHECK(
		seccomp_rule_add(
			ctx, SCMP_ACT_ALLOW, SCMP_SYS(mprotect), 1,
			SCMP_A2_64(SCMP_CMP_MASKED_EQ, ~(uint64_t)(PROT_READ | PROT_WRITE), 0)
		)
	);

	CHECK(seccomp_load(ctx));

	seccomp_release(ctx);

	return true;
}
