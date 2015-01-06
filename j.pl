#!/usr/bin/perl
=pod
STDIN slice and dicer

examples:

    $ jot 5 | j o5
    1   2   3   4   5

    $ jot 5| j p
    15

    $ echo 'data: {"a": {"b": "hello"}}' | j j[a.b]
    data:   hello
=cut

use strict;
use Getopt::Long qw(:config bundling);
use List::Util qw(first max maxstr min minstr reduce shuffle sum);

use Data::Dumper;

my $OPS = {
    'c' => sub {
        "cut -f${_[0]}";
    },
    'u' => sub {
        my $cmd = 'uniq';
        $cmd .= q( -c | perl -lpe 's/^\s+//;s/ /\t/') if $_[0] eq "c";
        $cmd;
    },
    's' => sub {
        my ($rev, $num, $col) = $_[0] =~ /(r?)(n?)([0-9]*)/;
        my $cmd = 'sort';
        $cmd .= ' -r' if $rev;
        $cmd .= ' -n' if $num;
        $cmd .= " -k $col" if $col;
        $cmd;
    },
    'h' => sub {
        'head -n' . ($_[0] or 10);
    },
    't' => sub {
        'tail -n' . ($_[0] or 10);
    },
    'p' => sub {
        q(perl -lane'$G[$_]+=$F[$_] for 0..$#F;END{print join "\t", @G}');
    },
    'a' => sub {
        q(perl -lane'$G[$_]+=$F[$_] for 0..$#F;$c++;
        END{@G=map{sprintf "%0.3f", $_/$c}@G;print join "\t", @G}');
    },
    'm' => sub {
        q(perl -lane'$F[$_]<$G[$_]||$.==1 and $G[$_]=$F[$_]
        for 0..$#F;END{print join "\t", @G}');
    },
    'M' => sub {
        q(perl -lane'$F[$_]>$G[$_]||$.==1 and $G[$_]=$F[$_]
        for 0..$#F;END{print join "\t", @G}');
    },
    '%' => sub {
        my $r = ($_[0] || 50) / 100.0;
        q(perl -lne'print if rand(0) < ).$r.q(');
    },
    '@' => sub {
        q(perl -e'use List::Util qw[shuffle];print for shuffle <STDIN>;');
    },
    'r' => sub {
        my ($regex, $replace, $icase, $g) = $_[0] =~ /\/(.*?)\/(.*?)\/(i?)(g?)/;
        qq(perl -lape's/$regex/$replace/$icase$g');
    },
    '/' => sub {
        my ($regex, $icase, $exclude) = $_[0] =~ /(.*?)\/(i?)(v?)/;
        $exclude = $exclude ? 'unless' : 'if';
        q(perl -lane'print ) . $exclude . qq(/$regex/$icase');
    },
    'q' => sub {
        q(perl -lane'print join "\t", map qq["$_"], @F');
    },
    'l' => sub {
        'less';
    },
    'o' => sub {
        my $cols = $_[0] || 8;
        if ($cols eq '-1') {
            return q(tr '\n' '\t');
        }
        else {
            q(perl -lane'BEGIN{$c=) .$cols. q(}push @a, @F;
            while(@a >= $c){
                @b = ();push @b, shift @a for 1..$c;
                print join("\t", @b);
            }
            END{print join "\t", @a if @a;}');
        }
    },
    'x' => sub {
        my ($rev, $ps) = $_[0] =~ /(r?)(p?)/;
        my $cmd = 'xxd';
        $cmd .= ' -r' if $rev;
        $cmd .= ' -p' if $ps;
        $cmd;
    },
    'j' => sub {
        my ($queries) = $_[0] =~ /\[(.*)\]/;
        q(python -c'import sys, json, re;
decoder = json.JSONDecoder(strict=False)
queries = ") . $queries . q(".split(",")
queries = [filter(None, x.split(".")) for x in queries]

def do_query(data, parts):
    if not isinstance(data, list):
        data = [data]
    for part in parts:
        frontier = []
        for datum in data:
            front = datum[part]
            if isinstance(front, list):
                frontier.extend(front)
            else:
                frontier.append(front)
        data = frontier
    for datum in data:
        if isinstance(datum, (list, dict)):
            yield json.dumps(datum, separators=",:")
        else:
            yield str(datum)

OPEN_RE = re.compile(r"[\[\{]")

def parse_line(line):
    found = False
    start_pos = - 1
    while True:
        match = OPEN_RE.search(line, start_pos + 1)
        if not match:
            return None, None, None
        start_pos = match.start()
        try:
            (data, end_pos) = decoder.raw_decode(line[start_pos:])
            break
        except:
            pass
    F = line[:start_pos].strip().split("\t")
    G = line[start_pos + end_pos:].strip().split("\t")
    return F, data, G

for line in sys.stdin:
    line = line.strip()
    F, data, G = parse_line(line)
    if data is not None:
        for parts in queries:
            try:
                F.extend(do_query(data, parts))
            except:
                pass
        F.extend(G)
        print "\t".join(F)
    else:
        print line
        ');
    }
};

my $delim = '\s+';
my $output_delim = "\t";
my $expr = '';
my $verbose = 0;

GetOptions(
    'delim|d=s' => \$delim,
    'output-delim|D=s' => \$output_delim,
    'expr|e=s' => \$expr,
    'verbose|v' => \$verbose
) or die "usage: $0 [--delim=<regex>] <expr>\n";

$expr .= join(' ', @ARGV);

my @ops = $expr =~ /(
    c[-,0-9]*|       #cut
    uc?|             #uniq
    sr?n?[0-9]*|     #sort
    h[0-9]*|         #head
    t[0-9]*|         #tail
    p|               #sum
    a|               #average
    m|               #min
    M|               #max
    %[0-9]*|         #sample
    @|              #shuffle
    r\/.*?\/.*?\/i?g?| #replace
    \/.*?\/i?v?|     #grep
    q|               #quote
    l|               #less
    o-?[0-9]*|       #column
    xr?p?|           #xxd
    j\[(?:,?[\._a-zA-Z0-9]+)*\]| #json
    \S               #fail
)/gx;

my @commands = ();
sub parse_op {
    my ($letter, $argv) = $_[0] =~ /(.)(.*)/;
    my $func = $OPS->{$letter} or die "unsupported operation: $letter\n";
    return ($letter, $argv, $func);
}

while(scalar(@ops)) {
    my $op = shift @ops;
    my ($letter, $argv, $func) = parse_op($op);
    push @commands, &{$func}($argv);
}

unless($commands[-1] =~ /^(less|xxd)/) {
    push @commands, q[perl -lape '$_=join"].$output_delim.q[",@F'];
}

my $commands = join ' | ', @commands;

print STDERR "$commands\n" if $verbose;

my $pid = open(WRITER, '|'.$commands);

for my $line (<STDIN>) {
    chomp $line;
    $line = join "\t", split qr/$delim/, $line;
    next unless $line;
    print WRITER "$line\n";
}
