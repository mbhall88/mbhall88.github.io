---
layout: post
title: "Cheap Parallelisation"
date: 2020-06-22
tags: [bioinformatics, benchmark, command-line-utilities, speed]
---


[TOC]: #

# Table of Contents
- [What is `fd`?](#what-is-fd)
- [Baby steps: finding our files](#baby-steps-finding-our-files)
- [Constructing execution commands](#constructing-execution-commands)
  - [Simple: counting characters in files](#simple-counting-characters-in-files)
  - [Intermediate: changing file extensions](#intermediate-changing-file-extensions)
  - [Advanced: redirecting stdout to a file within the command](#advanced-redirecting-stdout-to-a-file-within-the-command)
- [Putting it all together: Parallel MSA](#putting-it-all-together-parallel-msa)
- [Benchmark](#benchmark)
  - [Results](#results)
  - [Conclusion](#conclusion)
- [Final Remarks](#final-remarks)


# Motivation

I was recently creating a [`snakemake`][snakemake] pipeline and needed to write a
rule/process that would perform a multiple sequence alignment (MSA) on 2,582 fasta
files. Usually, it is easy to parallelise this kind of task using `snakemake`. To cut a
long story short; using `snakemake` to parallelise across the files was not feasible. I
knew there were ways of doing this kind of thing with tools such as
[`parallel`][parallel], [`xargs`][xargs], and [`find`][find], but I had never really
invested the time to get comfortable with them. This post is an attempt to document that
process using one of my favourite CLI tools: [`fd`][fd]. We'll see how `fd` can be used
to execute multiple MSAs (with MAFFT) simultaneously, and benchmark how much faster it is than
a conventional "synchronous" approach.

## What is `fd`?

Quoting from its GitHub repository:

> `fd` is a simple, fast and user-friendly alternative to `find`.

and I would certainly agree with that. For the sake of brevity, I won't dive into the
full range of what `fd` does, but please take a minute to have a quick look at [the
README][fd-readme] before reading on any further.

For the purposes of this post, the functionality of `fd` we are most interested in is
`-x, --exec` and `-j, --threads`.

```
    -x, --exec <cmd>
            Execute a command for each search result.
            All arguments following --exec are taken to be arguments to the command until the argument ';' is encountered.
            Each occurrence of the following placeholders is substituted by a path derived from the current search result before the command is
            executed:
              '{}':   path
              '{/}':  basename
              '{//}': parent directory
              '{.}':  path without file extension
              '{/.}': basename without file extension
              
    -j, --threads <num>
            Set number of threads to use for searching & executing (default: number of available CPU cores)
```

Using `--exec` and `--threads` together will allow us to run a given command on however
many threads we like.

## Baby steps: finding our files

The first thing we need to do before executing a command on multiple threads is to
*find* the files we want to operate on. The toy dataset I'll be using is eight small
fasta files. If you're going to follow along at home, you can download the data from
[here][example-data].

The directory tree we are working with is

```
.
├── fd_example
│  ├── f1.fa
│  ├── f2.fa
│  ├── f3.fa
│  ├── f4.fa
│  ├── f5.fa
│  ├── f6.fa
│  ├── f7.fa
│  └── f8.fa
└── msas
```

To find the fasta files with `fd`, we can use the following command

```sh
$ fd --extension fa . fd_example
fd_example/f1.fa
fd_example/f2.fa
fd_example/f3.fa
fd_example/f4.fa
fd_example/f5.fa
fd_example/f6.fa
fd_example/f7.fa
fd_example/f8.fa
```

`--extension` tells `fd` we want to filter out search results by the given extension -
`fa` in this case. (I'll use the abbreviated `-e` for this in subsequent commands).
Next, we tell `fd` the pattern we are looking for is `.` - i.e. anything. Lastly, we
want to search (recursively) under the `fd_example` directory.

An alternate solution for the above would be skipping the use of `--extension` and using
the pattern on its own

```sh
$ fd '\.fa$' fd_example
```

The pattern is a [regular expression][regex] this time that says "anything ending in `.fa`".

Personally, I like to make commands like this as easy for others, and myself in the
future, to understand. So I'll stick with the `--extension` method.

## Constructing execution commands

Now that we have a list of file paths, we need to do something with them. From earlier,
we can see that `--exec` takes a command, `<cmd>`. The `fd` docs have
[examples][fd-exec] of different conventions for writing these commands. This command
will be executed for *each* file path that `fd` finds.

### Simple: counting characters in files

We'll start with something easy like counting characters in each file using `wc`. [`wc`][wc]
is a command-line utility that counts lines, words, and bytes (characters) in files.

```sh
$ fd -e fa --exec wc -c '{}' \; . fd_example
3689 fd_example/f5.fa
2155 fd_example/f8.fa
7324 fd_example/f1.fa
2503 fd_example/f2.fa
1433 fd_example/f7.fa
5701 fd_example/f3.fa
1766 fd_example/f6.fa
2530 fd_example/f4.fa
```

Let's break down the juicy bit - **`--exec wc -c '{}' \;`**. We tell `fd` to execute the
command `wc -c` on `{}`. If we refresh our memories on the `--exec` docs, `{}` refers to
the path returned by `fd` (note: we add quotes around `{}` to prevent more complex paths
failing). The `\;` bit at the end just tells `fd` where the execution command ends.
Anything else after this is for `fd`, or the shell, to deal with.

An even more concise version of this command would be

```sh
$ fd -e fa -x wc -c \; . fd_example
```

as `fd` appends the path `{}` to the end of the command if we don't add it ourselves.


Ok, so that was pretty easy. Let's look at something a little more complicated.

### Intermediate: changing file extensions

As a (somewhat contrived) second example, we'll use the same approach to change the file
extensions on all our fasta files from `.fa` to `.fasta`.

```sh
$ fd -e fa --exec mv '{}' '{.}'.fasta \; . fd_example
$ ls fd_example
f1.fasta  f2.fasta  f3.fasta  f4.fasta  f5.fasta  f6.fasta  f7.fasta  f8.fasta
```

Then only new thing here is the use of `'{.}'`. Again, from the help menu, `{.}` gives
us the path *without* the file extension. So `fd_example/f1.fa` becomes `fd_example/f1`.

### Advanced: redirecting stdout to a file within the command

Trying to redirect the standard output of a command to a file turns out to be a little
more involved. For example, going with what we've seen so far, if we wanted to get the
sequence identifier for each sequence in a fasta file and write them to file, our
initial attempt might look like this

```sh
$ fd -e fa \
    --exec rg -P '^>(?P<id>[^\s]+)\s.*' --replace '$id' > '{/.}'.ids \; \
    . fd_example
```

In this command, we use [ripgrep][rg] (`rg`) to grab the identifiers for the file and
write them out to a file called `'{/.}'.ids`. The help menu for `fd` tells us that
`{/.}` is the path basename without the file extension. So `fd_example/f1.fa` becomes
`f1.ids`. However, when we run this, we get an error message like `zsh: no such file or
directory: {/.}.ids`. What is effectively happening here is that before this command
gets passed to `fd`, it is first interpreted by the shell. The shell thinks we are
trying to write the output from everything up until the [redirection operator][redirect]
`>` (i.e. `fd -e fa --exec rg -P '^>(?P<id>[^\s]+)\s.*' --replace '$id'`) to a file
called `'{/.}'.ids \; . fd_example`. The shell is correct, there is no file called
`{/.}.ids` - this syntax is only valid inside an `fd --exec` command.

We can fix this in one of two ways: inline bash command execution or a shell script.

#### Inline bash command

This option is pretty ugly - unless you're into one-liners...

```sh
$ fd -e fa \
    --exec sh -c "rg -P '^>(?P<id>[^\s]+)\s.*' --replace '\$id' '{}' > '{/.}'.ids" \; \
    . fd_example
```

As you can see, we need to invoke an inline shell command with `sh -c`. Part of the
awkwardness here is also having to escape some characters to prevent the shell from
trying to evaluate them, amongst other things. These inline commands can get very
cumbersome very fast!

#### Shell script

**Recommended**. For complex examples, such as the one we are working with, I would
suggest using this approach. The `fd` command itself does become slightly more obscure,
but if you name the script accordingly, it should still be self-explanatory.

Replicating our example from the above example, we create a script `extract_seq_id.sh`

```sh
#!/usr/bin/env sh
rg -P '^>(?P<id>[^\s]+)\s.*' --replace '$id' "$1" > "$2"
```

and then execute the script with `fd`.

```sh
$ fd -e fa \
   --exec sh extract_seq_id.sh '{}' '{/.}'.ids \; \
   . fd_example
```

Much neater!

If we take a look inside one of the output files, we should see the identifiers

```sh
$ cat f1.ids
fadD23+Rv3827c+Rv3828c
76c33157-d262-467c-960b-c21f8fa16991
```

## Putting it all together: Parallel MSA

Ok, armed with our `fd --exec` knowledge, let's parallelise multiple sequence alignment
on our samples and benchmark how much of a difference throwing more threads at `fd`
makes.

To perform the MSA, we are going to use [MAFFT][mafft]. MAFFT writes its output to
standard output. Luckily we know how to deal with this 😎. We'll write a script and then
execute that script with `fd`.

`msa.sh`

```sh
#!/usr/bin/env sh
mafft --thread 1 --auto "$1" > "$2"
```

*Note: we are only specifying one thread for benchmarking purposes.*

Our `fd` command will then be

```sh
$ fd -e fa --exec sh msa.sh '{}' msas/'{/.}'.msa.fa \; . fd_example
```

Our directory tree now looks like

```
.
├── fd_example
│  ├── f1.fa
│  ├── f2.fa
│  ├── f3.fa
│  ├── f4.fa
│  ├── f5.fa
│  ├── f6.fa
│  ├── f7.fa
│  └── f8.fa
├── msa.sh
└── msas
   ├── f1.msa.fa
   ├── f2.msa.fa
   ├── f3.msa.fa
   ├── f4.msa.fa
   ├── f5.msa.fa
   ├── f6.msa.fa
   ├── f7.msa.fa
   └── f8.msa.fa
```

## Benchmark

How much of a difference does more threads make? We'll benchmark various numbers of
threads using the tool [`hyperfine`][hyperfine] and its neat [parameter
scan][param-scan] functionality. The data used in this benchmarking is a little
different to the toy dataset. I have restricted the files to those above 9kb in size (80
files in total) to try and see the full effects of multiple threads. The 100 threads
option is just a roundabout way of saying "however many threads you can find." The
machine I ran this benchmark on has 16.

```sh
$ hyperfine -L threads 1,2,4,8,100 --export-markdown results.md \
    "fd -j {threads} -S +9k -e fa --exec sh msa.sh '{}' msas/'{/.}'.msa.fa \; . bench_data"
```

### Results

```
Benchmark #1: fd -j 1 -e fa -S +9k --exec sh msa.sh '{}' msas/'{/.}'.msa.fa \; . bench_data/
  Time (mean ± σ):     16.708 s ±  0.475 s    [User: 13.742 s, System: 6.550 s]
  Range (min … max):   15.972 s … 17.666 s    10 runs

Benchmark #2: fd -j 2 -e fa -S +9k --exec sh msa.sh '{}' msas/'{/.}'.msa.fa \; . bench_data/
  Time (mean ± σ):     10.003 s ±  0.064 s    [User: 15.850 s, System: 7.498 s]
  Range (min … max):    9.896 s … 10.115 s    10 runs

Benchmark #3: fd -j 4 -e fa -S +9k --exec sh msa.sh '{}' msas/'{/.}'.msa.fa \; . bench_data/
  Time (mean ± σ):      7.232 s ±  0.331 s    [User: 20.556 s, System: 10.231 s]
  Range (min … max):    6.943 s …  7.751 s    10 runs

Benchmark #4: fd -j 8 -e fa -S +9k --exec sh msa.sh '{}' msas/'{/.}'.msa.fa \; . bench_data/
  Time (mean ± σ):      6.118 s ±  0.233 s    [User: 22.905 s, System: 11.137 s]
  Range (min … max):    5.461 s …  6.250 s    10 runs

Benchmark #5: fd -j 100 -e fa -S +9k --exec sh msa.sh '{}' msas/'{/.}'.msa.fa \; . bench_data/
  Time (mean ± σ):      5.913 s ±  0.028 s    [User: 24.093 s, System: 11.508 s]
  Range (min … max):    5.880 s …  5.954 s    10 runs

Summary
  'fd -j 100 -e fa -S +9k --exec sh msa.sh '{}' msas/'{/.}'.msa.fa \; . bench_data/' ran
    1.03 ± 0.04 times faster than 'fd -j 8 -e fa -S +9k --exec sh msa.sh '{}' msas/'{/.}'.msa.fa \; . bench_data/'
    1.22 ± 0.06 times faster than 'fd -j 4 -e fa -S +9k --exec sh msa.sh '{}' msas/'{/.}'.msa.fa \; . bench_data/'
    1.69 ± 0.01 times faster than 'fd -j 2 -e fa -S +9k --exec sh msa.sh '{}' msas/'{/.}'.msa.fa \; . bench_data/'
    2.83 ± 0.08 times faster than 'fd -j 1 -e fa -S +9k --exec sh msa.sh '{}' msas/'{/.}'.msa.fa \; . bench_data/'
```

| Command                                                                            |       Mean [s] | Min [s] | Max [s] |    Relative |
|:-----------------------------------------------------------------------------------|---------------:|--------:|--------:|------------:|
| `fd -j 1 -e fa -S +9k --exec sh msa.sh '{}' msas/'{/.}'.msa.fa \; . bench_data/`   | 16.708 ± 0.475 |  15.972 |  17.666 | 2.83 ± 0.08 |
| `fd -j 2 -e fa -S +9k --exec sh msa.sh '{}' msas/'{/.}'.msa.fa \; . bench_data/`   | 10.003 ± 0.064 |   9.896 |  10.115 | 1.69 ± 0.01 |
| `fd -j 4 -e fa -S +9k --exec sh msa.sh '{}' msas/'{/.}'.msa.fa \; . bench_data/`   |  7.232 ± 0.331 |   6.943 |   7.751 | 1.22 ± 0.06 |
| `fd -j 8 -e fa -S +9k --exec sh msa.sh '{}' msas/'{/.}'.msa.fa \; . bench_data/`   |  6.118 ± 0.233 |   5.461 |   6.250 | 1.03 ± 0.04 |
| `fd -j 100 -e fa -S +9k --exec sh msa.sh '{}' msas/'{/.}'.msa.fa \; . bench_data/` |  5.913 ± 0.028 |   5.880 |   5.954 |        1.00 |

### Conclusion

The benchmark I have run here is a little contrived and doesn't really reflect the full
benefit of multiple threads in `fd`. The fasta files I am performing MSA on are quite
small/simple, so the benefit of multiple threads isn't quite as drastic as it would be
for more complex alignments. Part of the problem with benchmarking on more complex files
is the single-threaded commands run far too slow, and this is not intended to be a full
scale benchmarking post. For a real-world (anecdotal) example, it took ~3.5 minutes to
run MAFFT on my 2,582 fasta files using 16 threads. You can see an example of how I
embedded this in a `snakemake` pipeline [here][snakemake-example].

## Final Remarks

I hope this post was insightful and useful. In the future, I hope to write more posts
like this one (provided people find this one helpful) on whatever comes up in my work
that I think might be interesting to others. In the meantime, feel free to get in touch
if you have any questions or comments or complaints about this post.


[parallel]: https://www.gnu.org/software/parallel/
[wc]: https://linux.die.net/man/1/wc
[fd]: https://github.com/sharkdp/fd
[find]: https://www.gnu.org/software/findutils/
[fd-readme]: https://github.com/sharkdp/fd/blob/master/README.md
[snakemake]: https://snakemake.readthedocs.io/en/stable/
[fd-exec]: https://github.com/sharkdp/fd/blob/master/README.md#parallel-command-execution
[regex]: https://en.wikipedia.org/wiki/Regular_expression
[example-data]: https://github.com/mbhall88/mbhall88.github.io/tree/master/assets/data/fd_example.tar.gz
[rg]: https://github.com/BurntSushi/ripgrep
[mafft]: https://mafft.cbrc.jp/alignment/software/
[hyperfine]: https://github.com/sharkdp/hyperfine
[param-scan]: https://github.com/sharkdp/hyperfine#parameterized-benchmarks
[redirect]: https://pubs.opengroup.org/onlinepubs/9699919799.2016edition/basedefs/V1_chap03.html#tag_03_318
[xargs]: https://www.man7.org/linux/man-pages/man1/xargs.1.html
[snakemake-example]: https://github.com/mbhall88/head_to_head_pipeline/blob/9af773c7e5e8f861dbe05cd1e71300a856325ea2/data/H37Rv_PRG/Snakefile#L352-L379