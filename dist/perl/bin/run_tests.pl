#!/usr/bin/env perl
# Test runner for Perl backend

use strict;
use warnings;
use feature 'signatures';
no warnings 'experimental::signatures';
use File::Find;
use File::Basename;
use Time::HiRes qw(time);

require 'parable.pl';

sub find_test_files ($directory) {
    my @result;
    find(sub {
        push @result, $File::Find::name if /\.tests$/;
    }, $directory);
    return sort @result;
}

sub parse_test_file ($filepath) {
    open my $fh, '<', $filepath or die "Cannot open $filepath: $!";
    my @lines = <$fh>;
    close $fh;
    chomp @lines;

    my @tests;
    my $i = 0;
    my $n = scalar @lines;

    while ($i < $n) {
        my $line = $lines[$i];
        if ($line =~ /^#/ || $line =~ /^\s*$/) {
            $i++;
            next;
        }
        if ($line =~ /^=== (.*)/) {
            my $name = $1;
            my $start_line = $i + 1;
            $i++;
            my @input_lines;
            while ($i < $n && $lines[$i] ne '---') {
                push @input_lines, $lines[$i];
                $i++;
            }
            $i++ if $i < $n && $lines[$i] eq '---';
            my @expected_lines;
            while ($i < $n && $lines[$i] ne '---' && $lines[$i] !~ /^=== /) {
                push @expected_lines, $lines[$i];
                $i++;
            }
            $i++ if $i < $n && $lines[$i] eq '---';
            pop @expected_lines while @expected_lines && $expected_lines[-1] =~ /^\s*$/;

            my $test_input = join("\n", @input_lines);
            my $test_expected = join("\n", @expected_lines);
            push @tests, [$name, $test_input, $test_expected, $start_line];
        } else {
            $i++;
        }
    }
    return @tests;
}

sub normalize ($s) {
    $s =~ s/\s+/ /g;
    $s =~ s/^\s+//;
    $s =~ s/\s+$//;
    return $s;
}

sub run_test ($test_input, $test_expected) {
    my $extglob = 0;
    if ($test_input =~ s/^# \@extglob\n//) {
        $extglob = 1;
    }

    my $actual;
    eval {
        local $SIG{ALRM} = sub { die "timeout\n" };
        alarm(10);
        my $nodes = main::parse($test_input, $extglob);
        $actual = join(' ', map { $_->to_sexp() } @$nodes);
        alarm(0);
    };
    alarm(0);
    if ($@) {
        my $error = $@;
        if ($error eq "timeout\n") {
            return (0, '<timeout>', 'Test timed out after 10 seconds');
        }
        if (normalize($test_expected) eq '<error>') {
            return (1, '<error>', undef);
        }
        return (0, '<parse error>', $error);
    }

    if (normalize($test_expected) eq '<error>') {
        return (0, $actual, 'Expected parse error but got successful parse');
    }

    my $expected_norm = normalize($test_expected);
    my $actual_norm = normalize($actual);
    if ($expected_norm eq $actual_norm) {
        return (1, $actual, undef);
    } else {
        return (0, $actual, undef);
    }
}

sub print_usage {
    print "Usage: run_tests [options] [test_dir]\n";
    print "Options:\n";
    print "  -v, --verbose       Show PASS/FAIL for each test\n";
    print "  -f, --filter PAT    Only run tests matching PAT\n";
    print "  --max-failures N    Show at most N failures (0=unlimited, default=20)\n";
    print "  -h, --help          Show this help message\n";
}

sub main {
    my $test_dir;
    my $verbose = 0;
    my $filter_pattern;
    my $max_failures = 20;
    my $i = 0;
    while ($i < @ARGV) {
        my $arg = $ARGV[$i];
        if ($arg eq '-h' || $arg eq '--help') {
            print_usage();
            exit(0);
        } elsif ($arg eq '-v' || $arg eq '--verbose') {
            $verbose = 1;
        } elsif ($arg eq '-f' || $arg eq '--filter') {
            $i++;
            $filter_pattern = $ARGV[$i] if $i < @ARGV;
        } elsif ($arg eq '--max-failures') {
            $i++;
            $max_failures = int($ARGV[$i]) if $i < @ARGV;
        } elsif ($arg !~ /^-/) {
            $test_dir = $arg;
        }
        $i++;
    }

    die "Usage: run_tests <tests_dir>\n" unless defined $test_dir && -e $test_dir;

    my $start_time = time();
    my $total_passed = 0;
    my $total_failed = 0;
    my @failed_tests;

    my @test_files;
    if (-f $test_dir) {
        @test_files = ($test_dir);
    } else {
        @test_files = find_test_files($test_dir);
    }

    for my $filepath (@test_files) {
        my @tests = parse_test_file($filepath);
        my $rel_path = $filepath;
        if ($rel_path =~ m{/tests/}) {
            $rel_path =~ s{.*/tests/}{tests/};
        }

        for my $test (@tests) {
            my ($name, $test_input, $test_expected, $line_num) = @$test;

            if (defined $filter_pattern) {
                next unless $name =~ /\Q$filter_pattern\E/ || $rel_path =~ /\Q$filter_pattern\E/;
            }

            my $effective_expected = $test_expected;
            if (normalize($test_expected) eq '<infinite>') {
                $effective_expected = '<error>';
            }

            my ($passed, $actual, $error_msg) = run_test($test_input, $effective_expected);

            if ($passed) {
                $total_passed++;
                print "PASS $rel_path:$line_num $name\n" if $verbose;
            } else {
                $total_failed++;
                push @failed_tests, [$rel_path, $line_num, $name, $test_input, $test_expected, $actual, $error_msg];
                print "FAIL $rel_path:$line_num $name\n" if $verbose;
            }
        }
    }

    my $elapsed = time() - $start_time;

    if ($total_failed > 0) {
        print "=" x 60, "\n";
        print "FAILURES\n";
        print "=" x 60, "\n";
        my $show_count = $max_failures == 0 ? scalar(@failed_tests) : ($#failed_tests + 1 < $max_failures ? $#failed_tests + 1 : $max_failures);
        for my $i (0 .. $show_count - 1) {
            my $failure = $failed_tests[$i];
            my ($rel_path, $line_num, $name, $inp, $expected, $actual, $error_msg) = @$failure;
            print "\n$rel_path:$line_num $name\n";
            print "  Input:    '$inp'\n";
            print "  Expected: $expected\n";
            print "  Actual:   $actual\n";
            print "  Error:    $error_msg\n" if defined $error_msg;
        }
        if ($max_failures > 0 && $total_failed > $max_failures) {
            print "\n... and " . ($total_failed - $max_failures) . " more failures\n";
        }
    }

    printf "%d passed, %d failed in %.2fs\n", $total_passed, $total_failed, $elapsed;
    exit($total_failed > 0 ? 1 : 0);
}

main();
