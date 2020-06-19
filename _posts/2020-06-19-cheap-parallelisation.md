---
layout: post
title: "Cheap Parallelisation"
date: 2020-06-19
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


# Motivation

I was recently creating a [`snakemake`][snakemake] pipeline and needed to write a
rule/process that would perform a multiple sequence alignment (MSA) on 2,582 fasta files.
Usually, it is easy to parallelise this kind of task using `snakemake`. To cut a long
story short; using `snakemake` to parallelise across the files was not feasible. I knew
there were ways of doing this kind of thing with tools such as [`parallel`][parallel],
`xargs`, and [`find`][find], but I had never really invested the time to get comfortable
with them. This post is an attempt to document that process using one of my favourite
CLI tools: [`fd`][fd]. We'll see how `fd` can be used to execute multiple MSAs
simultaneously, and benchmark how much faster it is than a conventional "synchronous"
approach.

## What is `fd`?

Quoting from its GitHub repository:

> `fd` is a simple, fast and user-friendly alternative to `find`.

and I would certainly agree with that. For the sake of brevity, I won't dive into the
full range of what `fd` does, but please take a minute to have a quick look at [the
README][fd-readme] on the repository before reading on any further.

For the purposes of this post, the functionality of `fd` we are most interested in is
`-x, --exe` and `-j, --threads`.

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
fasta files. If you want to follow along at home, you can download the data from [here][example-data].

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

To find the fasta files with `fd` we can use the following command

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
`fa` in this case. (I'll use the abbreviated `-e` for this in subsequent commands). Next, we
tell `fd` the pattern we are looking for is `.` - i.e. anything. Lastly, we want to
search (recursively) under the `fd_example` directory.

An alternate solution for the above would be skipping the use of `--extension` and using
the pattern on its own

```sh
$ fd '\.fa$' fd_example
```

The pattern is a regular expressions this time that says "anything ending in `.fa`".

Personally, I like to make commands like this as easy for others, and myself in the
future, to understand. So I'll stick with the `--extension` method.

## Constructing execution commands

Now that we have a list of file paths, we need to do something with them. From earlier,
we can see that `--exec` takes a command, `<cmd>`. The `fd` docs have a nice
[example][fd-exec] of different conventions for writing these commands. This command
will be executed for *each*file path that `fd` finds.

### Simple: counting characters in files

We'll start with something easy like counting characters in each file using `wc`. `wc`
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

Let's break down the juicy bit - `--exec wc -c '{}' \;`. We tell `fd` to execute the
command `wc -c` on `{}`. If we refresh our memories on the `--exec` docs, `{}` refers to
the path returned by `fd`  (note: we add quotes around `{}` to prevent more complex paths failing). The `\;` bit at the end just tells `fd` that we have reached
the end of the execution command and anything else after this is for `fd` or the shell
to deal with.

An even more concise version of this command would be
```sh
$ fd -e fa -x wc -c \; . fd_example
```
as `fd` appends the path `{}` to the end of the command if we don't add it ourselves.


Ok, so that was pretty easy. Let's look at something a little more difficult.

### Intermediate: changing file extensions

As a (somewhat contrived) second example, we'll use the same approach to change the file
extensions on all our fasta files from `.fa` to `.fasta`.

```sh
$ fd -e fa --exec mv '{}' '{.}'.fasta \; . fd_example
$ ls fd_example
f1.fasta  f2.fasta  f3.fasta  f4.fasta  f5.fasta  f6.fasta  f7.fasta  f8.fasta
```

Then only new thing here is the use of `'{.}'`. Again, from the help menu, `{.}` gives
us the path without the file extension.

### Advanced: redirecting stdout to a file within the command

Trying to redirect the standard output of a command to a file turns out to be a litle
more complicated. For example, going with what we've seen so far, if we wanted to get
the sequence identifier for each sequence in eas of our fasta files and write them to a
file, our initial attempt might look like this

```sh
$ fd -e fa \
    --exec rg -P '^>(?P<id>[^\s]+)\s.*' --replace '$id' > '{/.}'.ids \; \
    . fd_example
```

In this command, we use [ripgrep][rg] (`rg`) to grab the identifiers for the file and
write them out to a file called `'{/.}'.ids`. The help menu for `fd` tells us that
`{/.}` is the path basename without the file extension. So `fd_example/f1.fa` becomes
`f1.ids`. However, when we run this, we get an error message like `zsh: no such file or
directory: {/.}.ids`. What is effectively happening here is that the shell thinks we are
trying to redirect the output from everything up until the `>` i.e. `fd -e fa --exec rg -P
'^>(?P<id>[^\s]+)\s.*' --replace '$id'` to a file called `'{/.}'.ids \; . fd_example`.
The shell is correct, there is no file called `{/.}.ids` - this syntax is only valid
inside an `fd --exec` command.

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
unwiedly very fast!

#### Shell script

**Recommended**. For complex examples, such as the one we are working with, I would
suggest using this approach. The `fd` command itself does become slightly more vague,
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

If we take a look inside one of the output files we shold see the identifiers

```sh
$ cat f1.ids
fadD23+Rv3827c+Rv3828c
76c33157-d262-467c-960b-c21f8fa16991
```

## Putting it all together: Parallel MSA

Ok, armed with our `fd --exec` knowledge, lets parallelise multiple sequence alignment
on our samples and benchmark how much of a difference throwing more threads at `fd` makes.

To perform the MSA we are going to use [MAFFT][mafft]. MAFFT writes its output to
standard output. Luckily we know how to deal with this 😎. We'll write a script and then
execute that script with `fd`.

`msa.sh`
```sh
#!/usr/bin/env sh
mafft --thread 1 --auto "$1" > "$2"
```

*Note: we are only specifying one thread here purely for the purposes of benchmarking.*

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
scan][param-scan] functionality.

```sh
$ hyperfine -L threads 1,2,4,8 \
    "fd -j {threads} -e fa --exec sh msa.sh '{}' msas/'{/.}'.msa.fa \; . fd_example"
```



[parallel]: https://www.gnu.org/software/parallel/
[fd]: https://github.com/sharkdp/fd
[find]: https://www.gnu.org/software/findutils/
[fd-readme]: https://github.com/sharkdp/fd/blob/master/README.md
[snakemake]: https://snakemake.readthedocs.io/en/stable/
[fd-exec]: https://github.com/sharkdp/fd/blob/master/README.md#parallel-command-execution
<!--[example-data]: #todo-->
[rg]: https://github.com/BurntSushi/ripgrep
[mafft]: https://mafft.cbrc.jp/alignment/software/
[hyperfine]: https://github.com/sharkdp/hyperfine
[param-scan]: https://github.com/sharkdp/hyperfine#parameterized-benchmarks