// Container PID 1 that waits for *all* other processes to exit before exiting.

#define _POSIX_C_SOURCE 200809L

#include <assert.h>
#include <errno.h>
#include <signal.h>
#include <spawn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/wait.h>

#define LEN(arr) (sizeof (arr) / sizeof (arr)[0])

extern char** environ;

int main(int argc, char* argv[]) {
	if (argc < 2) {
		fputs("Usage: init <program> <arg>...\n", stderr);
		return EXIT_FAILURE;
	}

	sigset_t blocked_signals, no_signals;
	{
		int r;
		r = sigfillset(&blocked_signals);
		assert(r == 0);
		r = sigemptyset(&no_signals);
		assert(r == 0);

		// signal list from github.com/krallin/tini
		constexpr int no_forward[] = {SIGFPE, SIGILL, SIGSEGV, SIGBUS, SIGABRT, SIGTRAP, SIGSYS, SIGTTIN, SIGTTOU};
		for (size_t i = 0; i < LEN(no_forward); i++) {
			r = sigdelset(&blocked_signals, no_forward[i]);
			assert(r == 0);
		}
	}

	if (sigprocmask(SIG_BLOCK, &blocked_signals, nullptr) != 0) {
		perror("init: sigprocmask failed");
		return EXIT_FAILURE;
	}

	pid_t main_pid;
	{
		int err;
		posix_spawnattr_t attr;
		if (
			   (err = posix_spawnattr_init(&attr)) != 0
			|| (err = posix_spawnattr_setflags(&attr, POSIX_SPAWN_SETSIGMASK)) != 0
			|| (err = posix_spawnattr_setsigmask(&attr, &no_signals)) != 0
		) {
			fprintf(stderr, "init: spawn attribute operations failed: %s\n", strerror(err));
			return EXIT_FAILURE;
		}

		err = posix_spawnp(&main_pid, argv[1], nullptr, &attr, argv + 1, environ);
		if (err != 0) {
			fprintf(stderr, "init: spawning process failed: %s\n", strerror(err));
			return EXIT_FAILURE;
		}

		(void)posix_spawnattr_destroy(&attr);
	}

	bool main_reaped = false;
	int main_exit_code = 1;
	for (;;) {
		int sig;
		{
			int err = sigwait(&blocked_signals, &sig);
			if (err != 0) {
				fprintf(stderr, "init: sigwait failed: %s\n", strerror(err));
				return EXIT_FAILURE;
			}
		}

		if (sig == SIGCHLD) {
			for (;;) {
				int s;
				pid_t c = waitpid((pid_t)-1, &s, WNOHANG);
				if (c == 0) break;
				if (c < 0) {
					if (errno == ECHILD) return main_exit_code;
					perror("init: waitpid failed");
					return EXIT_FAILURE;
				}
				if (!main_reaped && c == main_pid) {
					main_reaped = true;
					main_exit_code = WIFEXITED(s) ? WEXITSTATUS(s) : 128 + WTERMSIG(s);
				}
			}
		} else if (!main_reaped) {
			if (kill(main_pid, sig) != 0) {
				fprintf(stderr, "init: failed to forward signal %d: %s\n", sig, strerror(errno));
				return EXIT_FAILURE;
			}
		} else {
			fprintf(stderr, "init: ignored signal %d while waiting for reparented children to exit\n", sig);
		}
	}
}
