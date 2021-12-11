[![Shield](https://img.shields.io/github/workflow/status/stacscan/stacs/Check?label=Tests&style=flat-square)](https://github.com/stacscan/stacs/actions?workflow=Check)
[![Shield](https://img.shields.io/github/workflow/status/stacscan/stacs/Publish?label=Deploy&style=flat-square)](https://github.com/stacscan/stacs/actions?workflow=Publish)
[![Shield](https://img.shields.io/docker/pulls/stacscan/stacs?style=flat-square)](https://hub.docker.com/r/stacscan/stacs)
[![Shield](https://img.shields.io/docker/image-size/stacscan/stacs?style=flat-square)](https://hub.docker.com/r/stacscan/stacs/tags?page=1&ordering=last_updated)
[![Shield](https://img.shields.io/twitter/follow/stacscan?style=flat-square)](https://twitter.com/stacscan)
<p align="center">
    <br /><br />
    <img src="https://raw.githubusercontent.com/stacscan/stacs/main/docs/images/STACS-Logo-RGB.small.png">
</p>
<p align="center">
    <br />
    <b>Static Token And Credential Scanner</b>
    <br />
</p>

### What is it?

STACS is a [YARA](https://virustotal.github.io/yara/) powered static credential scanner
which suports binary file formats, analysis of nested archives, composable rulesets
and ignore lists, and SARIF reporting.

### What does STACS support?

Currently, STACS supports recursive unpacking of tarballs, gzips, bzips, zips, 7z, iso,
rpm and xz files. As STACS works on detected file types, rather than the filename,
propriatary file formats based on these types are automatically supported (such as
Docker images, Android APKs, and Java JAR fles).

### Who should use STACS?

STACS is designed for use by any teams who release binary artifacts. STACS provides
developers the ability to automatically check for accidental inclusion of static
credentials and key material in their releases.

However, this doesn't mean STACS can't help with SaaS applications, enterprise
software, or even source code!

As an example, STACS can be used to find static credentials in Docker images uploaded
to public and private container registries. It can also be used to find credentials
accidentally compiled in to executables, packages for mobile devices, and "enterprise
archives" - such as those used by Java application servers.

### How does it work?

STACS detects static credentials using "rule packs" provided to STACS when run. These
rule packs define a set of YARA rules to run against files provided to STACS. When a
match against a rule is found, a "finding" is generated. These findings represent
potential credentials inside of a file, and are reported on for a developer to remediate
or "ignore".

If the finding is found to be a false positive - that is, a match on something other
than a real credential - the developer can generate a set of "ignore lists" to ensure
that these matches don't appear in future reports.

The real power from STACS comes from the automatic detection and unpacking of nested
archives, and composable ignore lists and rule packs.

#### Ignore lists?

In order to allow flexible and collaborative usage, STACS supports composable ignore
lists. This allows for an ignore list to include other ignore lists which enable
composition of a "tree of ignores" based on organisational guidelines. These ignore
lists are especially useful in organisations where many of the same frameworks or
products are used. If a team has already marked a finding as a false positive, other
teams get the benefit of not having to triage the same finding.

#### Rule packs?

In the same manner as ignore lists, rule packs are also composable. This enables an
organisation to define a baseline set of rules for use by all teams, while still
allowing teams to maintain rulesets specific to their products.

### How do I use it?

The easiest way to use STACS is using the Docker images published to Docker Hub.
However, STACS can also be installed directly from Python's PyPI, or by cloning this
repository. See the relevant sections below to get started!

A cloud based service is coming soon which allows integration directly in build
and release pipelines to enable detection of static credentials before release!

#### Docker

Using the published images, STACS can be used to scan artifacts right away! The STACS
Docker images provides a number of volume mounts for files wanted to be scanned to be
mounted directly into the scan container.

As an example, to scan everything in the current folder, the following command can be
run (Docker must be installed).

```
docker run \
    --rm \
    --mount type=bind,source=$(pwd),target=/mnt/stacs/input \
    stacscan/stacs:latest
```

By default, STACS will output any findings in SARIF format directly to STDOUT and in
order to keep things orderly, all log messages will be sent to STDERR. For more advanced
use cases, a number of other volume mounts are provided. These allow the user to control
the rule packs, ignore lists, and a cache directories to use.

#### PyPi

STACS can also be installed directly from Python's PyPi. This provides a `stacs` command
which can then be used by developers to scan projects directly in their local
development environments.

STACS can be installed directly from PyPi using:

```
pip install stacs
```

**Please Note:** The PyPi release of STACS does not come with any rules. These will also
need to be cloned from the [community rules repository](https://github.com/stacscan/stacs-rules)
for STACS to work!

### FAQ

#### Is there a hosted version of STACS?

Not yet. However, there are plans for a hosted version of STACS which can be easily
integrated into existing build systems, and which contains additional prebuilt rule
packs and ignore lists.

#### What do I do about false positives?

Unfortunately, false positives are an inevitable side effect during the detection of
static credentials. If rules are too granular then rule maintenance becomes a burden
and STACS may miss credentials. If rules are too coarse then STACS may generate too
many false positives!

In order to assist, STACS provides a number of tools to assist with reducing the number
of false positives which make it into final reports.

Primarily, STACS provides a mechanism which allows users to define composable ignore
lists which allow a set of findings to be "ignored". These rules can be as coarse as
ignoring all files based on a pattern, or as granular as a specific finding on a
particular line of a file.

This information is automatically propagated through into reports, so "ignored" findings
will be marked as "suppressed" in SARIF output while also including the reason for the
ignore in the output for tracking.

#### How do I view the results?

Currently, the only output format is SARIF v2.1.0. There are a number of viewers
available which make this data easier to read, such as [this great web based viewer from](https://microsoft.github.io/sarif-web-component/) Microsoft. An example of the findings from a Docker container
image has been included below:

![Microsoft SARIF Viewer Output](https://raw.githubusercontent.com/stacscan/stacs/main/docs/images/SARIF-Viewer-Example.png)

#### The performance is really, really bad when running in Docker on macOS!

Unfortunately, this appears to be due to a limitation of Docker Desktop for Mac. I/O
for bind mounts [is really, really slow](https://github.com/docker/for-mac/issues/3677).
