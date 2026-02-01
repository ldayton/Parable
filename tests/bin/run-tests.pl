#!/usr/bin/env perl
# Simple test runner for Perl backend. No dependencies beyond parable itself.

use strict;
use warnings;
use feature 'signatures';
no warnings 'experimental::signatures';
use File::Find;
use File::Basename;
use Time::HiRes qw(time);

# Import parable (it's a plain .pl file, not a module)
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
        # Skip comments and blank lines
        if ($line =~ /^#/ || $line =~ /^\s*$/) {
            $i++;
            next;
        }
        # Test header
        if ($line =~ /^=== (.*)/) {
            my $name = $1;
            my $start_line = $i + 1;
            $i++;
            # Collect input until ---
            my @input_lines;
            while ($i < $n && $lines[$i] ne '---') {
                push @input_lines, $lines[$i];
                $i++;
            }
            # Skip ---
            $i++ if $i < $n && $lines[$i] eq '---';
            # Collect expected until ---, next test, or EOF
            my @expected_lines;
            while ($i < $n && $lines[$i] ne '---' && $lines[$i] !~ /^=== /) {
                push @expected_lines, $lines[$i];
                $i++;
            }
            # Skip --- end marker
            $i++ if $i < $n && $lines[$i] eq '---';
            # Strip trailing blank lines from expected
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
    # Check for @extglob directive
    my $extglob = 0;
    if ($test_input =~ s/^# \@extglob\n//) {
        $extglob = 1;
    }

    my $actual;
    eval {
        my $nodes = main::parse($test_input, $extglob);
        $actual = join(' ', map { $_->to_sexp() } @$nodes);
    };
    if ($@) {
        my $error = $@;
        if (normalize($test_expected) eq '<error>') {
            return (1, '<error>', undef);
        }
        return (0, '<parse error>', $error);
    }

    # If we expected an error but got a successful parse, that's a failure
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

sub main {
    my $script_dir = dirname(__FILE__);
    my $test_dir = dirname($script_dir);  # tests/
    my $repo_root = dirname($test_dir);

    # Parse arguments
    my $verbose = 0;
    my $filter_pattern;
    my $i = 0;
    while ($i < @ARGV) {
        my $arg = $ARGV[$i];
        if ($arg eq '-v' || $arg eq '--verbose') {
            $verbose = 1;
        } elsif ($arg eq '-f' || $arg eq '--filter') {
            $i++;
            $filter_pattern = $ARGV[$i] if $i < @ARGV;
        } elsif (-e $arg) {
            $test_dir = $arg;
        }
        $i++;
    }

    # Find and run tests
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
        $rel_path =~ s/^\Q$repo_root\E\/?//;

        for my $test (@tests) {
            my ($name, $test_input, $test_expected, $line_num) = @$test;

            # Apply filter
            if (defined $filter_pattern) {
                next unless $name =~ /\Q$filter_pattern\E/ || $rel_path =~ /\Q$filter_pattern\E/;
            }

            # Treat <infinite> as <error>
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

    # Print summary
    print "\n";
    if ($total_failed > 0) {
        print "=" x 60, "\n";
        print "FAILURES\n";
        print "=" x 60, "\n";
        for my $failure (@failed_tests) {
            my ($rel_path, $line_num, $name, $inp, $expected, $actual, $error_msg) = @$failure;
            print "\n$rel_path:$line_num $name\n";
            print "  Input:    '$inp'\n";
            print "  Expected: $expected\n";
            print "  Actual:   $actual\n";
            print "  Error:    $error_msg\n" if defined $error_msg;
        }
        print "\n";
    }

    printf "%d passed, %d failed in %.2fs\n", $total_passed, $total_failed, $elapsed;

    exit($total_failed > 0 ? 1 : 0);
}

main();
