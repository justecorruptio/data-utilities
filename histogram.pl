#!/usr/bin/perl
=pod
A simple script to display a pretty histogram based on values read from STDIN.
=cut

use strict;
use Getopt::Long qw(:config bundling);
use List::Util qw(first max maxstr min minstr reduce shuffle sum);

binmode(STDOUT, ':utf8');

my @vals = <STDIN>;

my $min = min @vals;
my $max = max @vals;
my $buckets = 20;
my $width = 60;
my $log;

GetOptions(
    'buckets|b=i' => \$buckets,
    'min|m=f' => \$min,
    'max|M=f' => \$max,
    'width|w=i' => \$width,
    'log|l' => \$log
) or die "usage: $0 [--buckets=N] [--min=N] [--max=N] [--width=N] [--log]\n";

my $step = ($max - $min) * 1.0 / $buckets;

my @hist = ();
for my $val (@vals){
    $hist[$step && min(($val - $min) / $step, $buckets - 1)] ++;
}

my @disp = $log ? map log($_ + 1), @hist : @hist;

my $max_width = 1.0 * max(@disp) || 1;

for my $i (0 .. $buckets - 1){
    my $x = $disp[$i] * $width / $max_width;
    my $r = int(($x - int($x)) * 8);

    printf "%6.2f ", $i * $step + $min;
    print "\x1b[36m" if -t STDOUT;
    print chr(0x2589) x int($x);
    print chr(int(0x258f - $r + 1)) if $r;
    print "\x1b[0m" if -t STDOUT;
    print " ${hist[$i]}\n";
}
