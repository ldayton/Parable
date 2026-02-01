// Test runner for the C parser. Mirrors run-tests.py.
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>
#include <sys/stat.h>
#include <ctype.h>
#include <time.h>

#include "parable.c"

#define MAX_PATH 4096
#define MAX_FILES 10000
#define MAX_TESTS 50000

typedef struct {
    char *name;
    char *input;
    char *expected;
    int line_num;
} TestCase;

typedef struct {
    char *rel_path;
    int line_num;
    char *name;
    char *input;
    char *expected;
    char *actual;
    char *err;
} TestResult;

static char *test_files[MAX_FILES];
static int num_test_files = 0;
static TestResult failed_tests[MAX_TESTS];
static int num_failed = 0;

static char *strdup_safe(const char *s) {
    if (!s) return NULL;
    char *d = malloc(strlen(s) + 1);
    if (d) strcpy(d, s);
    return d;
}

static char *read_file(const char *path) {
    FILE *f = fopen(path, "r");
    if (!f) return NULL;
    fseek(f, 0, SEEK_END);
    long len = ftell(f);
    fseek(f, 0, SEEK_SET);
    char *buf = malloc(len + 1);
    if (!buf) { fclose(f); return NULL; }
    size_t read = fread(buf, 1, len, f);
    buf[read] = '\0';
    fclose(f);
    return buf;
}

static int cmp_str(const void *a, const void *b) {
    return strcmp(*(const char **)a, *(const char **)b);
}

static void find_test_files_recursive(const char *dir) {
    DIR *d = opendir(dir);
    if (!d) return;
    struct dirent *ent;
    while ((ent = readdir(d)) != NULL) {
        if (ent->d_name[0] == '.') continue;
        char path[MAX_PATH];
        snprintf(path, sizeof(path), "%s/%s", dir, ent->d_name);
        struct stat st;
        if (stat(path, &st) != 0) continue;
        if (S_ISDIR(st.st_mode)) {
            find_test_files_recursive(path);
        } else if (S_ISREG(st.st_mode)) {
            size_t len = strlen(ent->d_name);
            if (len > 6 && strcmp(ent->d_name + len - 6, ".tests") == 0) {
                if (num_test_files < MAX_FILES) {
                    test_files[num_test_files++] = strdup_safe(path);
                }
            }
        }
    }
    closedir(d);
}

static void find_test_files(const char *dir) {
    num_test_files = 0;
    find_test_files_recursive(dir);
    qsort(test_files, num_test_files, sizeof(char *), cmp_str);
}

static char **split_lines(const char *s, int *count) {
    int cap = 256;
    char **lines = malloc(cap * sizeof(char *));
    *count = 0;
    const char *start = s;
    while (*s) {
        if (*s == '\n') {
            int len = s - start;
            char *line = malloc(len + 1);
            memcpy(line, start, len);
            line[len] = '\0';
            if (*count >= cap) {
                cap *= 2;
                lines = realloc(lines, cap * sizeof(char *));
            }
            lines[(*count)++] = line;
            start = s + 1;
        }
        s++;
    }
    if (start < s) {
        int len = s - start;
        char *line = malloc(len + 1);
        memcpy(line, start, len);
        line[len] = '\0';
        if (*count >= cap) {
            cap *= 2;
            lines = realloc(lines, cap * sizeof(char *));
        }
        lines[(*count)++] = line;
    }
    return lines;
}

static void free_lines(char **lines, int count) {
    for (int i = 0; i < count; i++) free(lines[i]);
    free(lines);
}

static char *join_lines(char **lines, int start, int end) {
    if (start >= end) return strdup_safe("");
    size_t total = 0;
    for (int i = start; i < end; i++) {
        total += strlen(lines[i]) + 1;
    }
    char *result = malloc(total);
    result[0] = '\0';
    for (int i = start; i < end; i++) {
        strcat(result, lines[i]);
        if (i < end - 1) strcat(result, "\n");
    }
    return result;
}

static TestCase *parse_test_file(const char *filepath, int *num_tests) {
    char *content = read_file(filepath);
    if (!content) { *num_tests = 0; return NULL; }
    int line_count;
    char **lines = split_lines(content, &line_count);
    free(content);
    int cap = 256;
    TestCase *tests = malloc(cap * sizeof(TestCase));
    *num_tests = 0;
    int i = 0;
    while (i < line_count) {
        char *line = lines[i];
        if (line[0] == '#' || strlen(line) == 0 || line[0] == '\0') {
            int all_space = 1;
            for (char *c = line; *c; c++) if (!isspace(*c)) { all_space = 0; break; }
            if (all_space || line[0] == '#') { i++; continue; }
        }
        if (strncmp(line, "=== ", 4) == 0) {
            char *name = strdup_safe(line + 4);
            // trim
            char *end = name + strlen(name) - 1;
            while (end > name && isspace(*end)) *end-- = '\0';
            int start_line = i + 1;
            i++;
            int input_start = i;
            while (i < line_count && strcmp(lines[i], "---") != 0) i++;
            int input_end = i;
            if (i < line_count && strcmp(lines[i], "---") == 0) i++;
            int exp_start = i;
            while (i < line_count && strcmp(lines[i], "---") != 0 && strncmp(lines[i], "=== ", 4) != 0) i++;
            int exp_end = i;
            if (i < line_count && strcmp(lines[i], "---") == 0) i++;
            // trim trailing blank lines from expected
            while (exp_end > exp_start) {
                char *l = lines[exp_end - 1];
                int blank = 1;
                for (char *c = l; *c; c++) if (!isspace(*c)) { blank = 0; break; }
                if (!blank) break;
                exp_end--;
            }
            if (*num_tests >= cap) {
                cap *= 2;
                tests = realloc(tests, cap * sizeof(TestCase));
            }
            tests[*num_tests].name = name;
            tests[*num_tests].input = join_lines(lines, input_start, input_end);
            tests[*num_tests].expected = join_lines(lines, exp_start, exp_end);
            tests[*num_tests].line_num = start_line;
            (*num_tests)++;
        } else {
            i++;
        }
    }
    free_lines(lines, line_count);
    return tests;
}

static char *normalize(const char *s) {
    size_t len = strlen(s);
    char *result = malloc(len + 1);
    int j = 0;
    int in_space = 1;
    for (size_t i = 0; i < len; i++) {
        if (isspace((unsigned char)s[i])) {
            if (!in_space) {
                result[j++] = ' ';
                in_space = 1;
            }
        } else {
            result[j++] = s[i];
            in_space = 0;
        }
    }
    if (j > 0 && result[j-1] == ' ') j--;
    result[j] = '\0';
    return result;
}

// Symbols from parable.c (included above, so already visible)

static void run_test(const char *test_input, const char *test_expected,
                     int *passed, char **actual, char **err_msg) {
    int extglob = 0;
    const char *input = test_input;
    if (strncmp(input, "# @extglob\n", 11) == 0) {
        extglob = 1;
        input = input + 11;
    }
    g_parse_error = 0;
    g_error_msg[0] = '\0';
    Vec_Node nodes = parse(input, extglob);
    if (g_parse_error) {
        char *exp_norm = normalize(test_expected);
        if (strcmp(exp_norm, "<error>") == 0) {
            *passed = 1;
            *actual = strdup_safe("<error>");
            *err_msg = NULL;
        } else {
            *passed = 0;
            *actual = strdup_safe("<parse error>");
            *err_msg = strdup_safe(g_error_msg);
        }
        free(exp_norm);
        return;
    }
    // Build result string
    size_t result_cap = 4096;
    char *result = malloc(result_cap);
    result[0] = '\0';
    for (int64_t i = 0; i < nodes.len; i++) {
        const char *sexp = Node_to_sexp(nodes.data[i]);
        if (i > 0) strcat(result, " ");
        size_t needed = strlen(result) + strlen(sexp) + 2;
        if (needed > result_cap) {
            result_cap = needed * 2;
            result = realloc(result, result_cap);
        }
        strcat(result, sexp);
        // sexp is arena-allocated, no need to free
    }
    // nodes is arena-allocated, no need to free
    char *exp_norm = normalize(test_expected);
    if (strcmp(exp_norm, "<error>") == 0) {
        *passed = 0;
        *actual = result;
        *err_msg = strdup_safe("Expected parse error but got successful parse");
        free(exp_norm);
        return;
    }
    char *act_norm = normalize(result);
    if (strcmp(exp_norm, act_norm) == 0) {
        *passed = 1;
    } else {
        *passed = 0;
    }
    *actual = result;
    *err_msg = NULL;
    free(exp_norm);
    free(act_norm);
}

int main(int argc, char **argv) {
    int verbose = 0;
    char *filter_pattern = NULL;
    char *test_dir = NULL;
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-v") == 0 || strcmp(argv[i], "--verbose") == 0) {
            verbose = 1;
        } else if ((strcmp(argv[i], "-f") == 0 || strcmp(argv[i], "--filter") == 0) && i + 1 < argc) {
            filter_pattern = argv[++i];
        } else if (argv[i][0] != '-') {
            test_dir = argv[i];
        }
    }
    if (!test_dir) {
        test_dir = "tests";
        struct stat st;
        if (stat(test_dir, &st) != 0) {
            test_dir = "../tests";
        }
    }
    struct stat st;
    if (stat(test_dir, &st) != 0) {
        fprintf(stderr, "Could not find tests directory\n");
        return 1;
    }
    clock_t start_time = clock();
    int total_passed = 0;
    int total_failed = 0;
    num_failed = 0;
    find_test_files(test_dir);
    for (int f = 0; f < num_test_files; f++) {
        int num_tests;
        TestCase *tests = parse_test_file(test_files[f], &num_tests);
        // Compute relative path
        char *rel_path = test_files[f];
        char *tests_pos = strstr(rel_path, "/tests/");
        if (tests_pos) rel_path = tests_pos + 1;
        for (int t = 0; t < num_tests; t++) {
            TestCase *tc = &tests[t];
            if (filter_pattern) {
                if (!strstr(tc->name, filter_pattern) && !strstr(rel_path, filter_pattern)) {
                    continue;
                }
            }
            // Treat <infinite> as <error>
            char *effective_expected = tc->expected;
            char *exp_norm = normalize(tc->expected);
            int free_effective = 0;
            if (strcmp(exp_norm, "<infinite>") == 0) {
                effective_expected = "<error>";
                free_effective = 0;
            }
            free(exp_norm);
            int passed;
            char *actual;
            char *err_msg;
            run_test(tc->input, effective_expected, &passed, &actual, &err_msg);
            if (passed) {
                total_passed++;
                if (verbose) {
                    printf("PASS %s:%d %s\n", rel_path, tc->line_num, tc->name);
                }
            } else {
                total_failed++;
                if (num_failed < MAX_TESTS) {
                    failed_tests[num_failed].rel_path = strdup_safe(rel_path);
                    failed_tests[num_failed].line_num = tc->line_num;
                    failed_tests[num_failed].name = strdup_safe(tc->name);
                    failed_tests[num_failed].input = strdup_safe(tc->input);
                    failed_tests[num_failed].expected = strdup_safe(tc->expected);
                    failed_tests[num_failed].actual = actual;
                    failed_tests[num_failed].err = err_msg;
                    num_failed++;
                }
                if (verbose) {
                    printf("FAIL %s:%d %s\n", rel_path, tc->line_num, tc->name);
                }
            }
            if (free_effective && effective_expected != tc->expected) {
                free(effective_expected);
            }
        }
        // Free tests
        for (int t = 0; t < num_tests; t++) {
            free(tests[t].name);
            free(tests[t].input);
            free(tests[t].expected);
        }
        free(tests);
    }
    double elapsed = (double)(clock() - start_time) / CLOCKS_PER_SEC;
    if (total_failed > 0) {
        printf("============================================================\n");
        printf("FAILURES\n");
        printf("============================================================\n");
        int show_count = num_failed < 20 ? num_failed : 20;
        for (int i = 0; i < show_count; i++) {
            TestResult *f = &failed_tests[i];
            printf("\n%s:%d %s\n", f->rel_path, f->line_num, f->name);
            printf("  Input:    \"%s\"\n", f->input);
            printf("  Expected: %s\n", f->expected);
            printf("  Actual:   %s\n", f->actual);
            if (f->err) {
                printf("  Error:    %s\n", f->err);
            }
        }
        if (total_failed > 20) {
            printf("\n... and %d more failures\n", total_failed - 20);
        }
    }
    printf("%d passed, %d failed in %.2fs\n", total_passed, total_failed, elapsed);
    return total_failed > 0 ? 1 : 0;
}
