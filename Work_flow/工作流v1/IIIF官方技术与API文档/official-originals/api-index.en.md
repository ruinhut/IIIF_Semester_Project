<div class="section hero is-primary"
style="background-image: linear-gradient(to bottom, rgba(0, 25, 39, 0.68), rgba(0, 25, 39, 0.68)), url('/api');
  background-size: cover;
  background-position: bottom center;
  background-attachment: fixed;
  ">

<div class="hero-head">

<div class="container">

<div class="navbar-brand">

<a href="https://iiif.io/" class="navbar-item"><img
src="/api/assets/images/logos/logo-sm.png" height="28"
alt="IIIF logo" /> <span class="brand-title">International Image
Interoperability Framework</span></a>

<div class="navbar-burger" data-target="navbar"
onclick="document.querySelector('.navbar-menu').classList.toggle('is-active');">

</div>

</div>

<div class="navbar-menu">

<div class="navbar-end">

<a href="https://iiif.io/" class="navbar-item">Home</a>
<a href="https://iiif.io/demos" class="navbar-item">Demos</a>
<a href="https://iiif.io/events" class="navbar-item">Events</a>
<a href="https://iiif.io/news" class="navbar-item">News</a>

<div class="navbar-item has-dropdown is-hoverable">

<a href="https://iiif.io/get-involved" class="navbar-link">Get
Involved</a>

<div class="navbar-dropdown is-boxed is-active">

<a href="https://iiif.io/community/" class="navbar-item">Community</a>
<a href="https://iiif.io/community/consortium"
class="navbar-item">Consortium</a>
<a href="https://iiif.io/newsletter" class="navbar-item">Join
Newsletter</a> <a href="https://iiif.io/get-involved/outreach-materials"
class="navbar-item">Outreach Materials</a>

</div>

</div>

<div class="navbar-item has-dropdown is-hoverable">

<a href="https://iiif.io/get-started" class="navbar-link">Get
Started</a>

<div class="navbar-dropdown is-boxed is-active">

<a href="https://iiif.io/get-started/how-iiif-works"
class="navbar-item">How IIIF Works</a>
<a href="https://iiif.io/community/ambassadors/"
class="navbar-item">IIIF Ambassadors</a>
<a href="https://iiif.io/guides" class="navbar-item">Guides</a>
<a href="/api" class="navbar-item">APIs &amp; Documentation</a>
<a href="https://iiif.io/get-started/cookbook"
class="navbar-item">Cookbooks</a>
<a href="https://iiif.io/get-started/training"
class="navbar-item">Training</a>

</div>

</div>

</div>

</div>

</div>

</div>

<div class="hero-body container">

- [Get Started](https://iiif.io/get-started)
- [APIs & Documentation](/api/)

<div class="container has-text-centered">

# API Specifications - International Image Interoperability Framework™

</div>

</div>

</div>

<div id="main" class="section">

<div class="container-block no-padding is-max-desktop">

<div class="columns is-max-desktop">

<div class="aside column is-one-quarter api-sidebar-container"
data-markdown="1">

<div class="toc-sidebar sticky">

- [Current specifications](#current-specifications)
- [Draft specifications](#draft-specifications)
  - [Feedback requested](#feedback)
- [Approved extensions](#approved-extensions)
- [Community translations](#community-translations)
- [Community cookbook](#community-cookbook)
- [Validators](#validators)
- [Older versions](#older-versions)
- [Notes](#notes)
- [Process](#process)

</div>

</div>

<div class="column is-three-quarters content api-content"
data-markdown="1">

## Current specifications <a href="#current-specifications" class="anchorClass"></a>

| API | Current Version | Description |
|----|----|----|
| Image API | [3.0.0](/api/image/3.0/) | The IIIF Image API specifies a web service that returns an image in response to a standard HTTP(S) request. The URI can specify the region, size, rotation, quality characteristics and format of the requested image. |
| Presentation API | [3.0.0](/api/presentation/3.0/) | The IIIF Presentation API provides the information necessary to allow a rich, online viewing environment for compound digital objects to be presented to a human user, often in conjunction with the IIIF Image API. |
| Authorization Flow API | [2.0.0](/api/auth/2.0/) | The IIIF Authorization Flow specification describes a set of workflows for guiding the user through an existing access control system. |
| Change Discovery API | [1.0.0](/api/discovery/1.0/) | The IIIF Change Discovery API provides the information needed to discover and make use of IIIF resources. |
| Content Search API | [2.0.0](/api/search/2.0/) | The IIIF Content Search API specification lays out the interoperability mechanism for performing searches of text annotations associated with an object within the IIIF context. |
| Content State API | [1.0.0](/api/content-state/1.0/) | The IIIF Content State API provides a way to refer to a IIIF Presentation API resource, or a part of a resource, in a compact format that can be used to initialize the view of that resource in any client. |

## Draft specifications <a href="#draft-specifications" class="anchorClass"></a>

| <span class="abbr" title="Application Programming Interface">API</span> | Draft Version (Status) |
|----|----|
| Presentation <span class="abbr" title="Application Programming Interface">API</span> | [4.0.0](/api/presentation/4.0/) (Release candidate) |

### Feedback requested <a href="#feedback" class="anchorClass"></a>

We welcome feedback on all <span class="abbr"
title="International Image Interoperability Framework">IIIF</span>
Specifications. Please send any feedback to
<iiif-discuss@googlegroups.com>.

## Approved extensions <a href="#approved-extensions" class="anchorClass"></a>

Please see the [Registry of
Extensions](/api/registry/ "IIIF Extension Registry") for full details
on how extensions work and the process for creating them.

Currently, there are three formally published extensions available for
use with the Presentation <span class="abbr"
title="Application Programming Interface">API</span>.

| Presentation <span class="abbr" title="Application Programming Interface">API</span> Extensions | Description |
|----|----|
| [navPlace Extension](/api/extension/navplace/) | This <span class="abbr" title="International Image Interoperability Framework">IIIF</span> Presentation 3 <span class="abbr" title="Application Programming Interface">API</span> extension defines a new property, navPlace, which is defined by earthbound geographic coordinates in the form of GeoJSON-LD. |
| [Text Granularity Extension](/api/extension/text-granularity/) | This extension recommends a pattern for indicating the level of text granularity for an annotation related to optical character recognition (OCR) software, manual transcription, and existing digitized text. |
| [Georeference Extension](/api/extension/georef/) | This extension leverages Web Annotations to provide a pattern for georeferencing <span class="abbr" title="International Image Interoperability Framework">IIIF</span> Presentation 3 <span class="abbr" title="Application Programming Interface">API</span> Canvases as well as images served through the <span class="abbr" title="International Image Interoperability Framework">IIIF</span> Image <span class="abbr" title="Application Programming Interface">API</span>. |

## Community translations <a href="#community-translations" class="anchorClass"></a>

| <span class="abbr" title="Application Programming Interface">API</span> | Version | Translation |
|----|----|----|
| Image <span class="abbr" title="Application Programming Interface">API</span> | 3.0 | [Japanese](http://www.asahi-net.or.jp/~ax2s-kmtn/ref/iiif/apiimage3.0.html), [Chinese](https://www.yuque.com/iiifchina/df4qfk/fwybkl) |
| Image <span class="abbr" title="Application Programming Interface">API</span> | 2.1 | [Japanese](http://www.asahi-net.or.jp/~ax2s-kmtn/ref/iiif/apiimage2.1.html) |
| Presentation <span class="abbr" title="Application Programming Interface">API</span> | 3.0 | [Chinese](https://www.yuque.com/iiifchina/df4qfk/gpf6od) |
| Presentation <span class="abbr" title="Application Programming Interface">API</span> | 2.1 | [Japanese](http://www.asahi-net.or.jp/~ax2s-kmtn/ref/iiif/apipresentation2.1.html) |
| Content Search <span class="abbr" title="Application Programming Interface">API</span> | 1.0 | [Japanese](http://www.asahi-net.or.jp/~ax2s-kmtn/ref/iiif/searchapi1.0.html), [Chinese](https://www.yuque.com/iiifchina/df4qfk/ygbnck) |
| Authentication <span class="abbr" title="Application Programming Interface">API</span> | 1.0 | [Japanese](http://www.asahi-net.or.jp/~ax2s-kmtn/ref/iiif/apiauthentication1.0.html), [Chinese](https://www.yuque.com/iiifchina/df4qfk/vkxifz) |
| Discovery <span class="abbr" title="Application Programming Interface">API</span> | 1.0 | [Chinese](https://www.yuque.com/iiifchina/df4qfk/hdb26g) |
| Content State <span class="abbr" title="Application Programming Interface">API</span> | 0.9 | [Chinese](https://www.yuque.com/iiifchina/df4qfk/wysy7i) |
| NavPlace Extension |   | [Chinese](https://www.yuque.com/iiifchina/df4qfk/xh0bna) |

**Translation note**\
Please note that the <span class="abbr"
title="International Image Interoperability Framework">IIIF</span>
community does not guarantee the accuracy of any translation. They are
linked to for information purposes only, and any discrepancies with the
specifications are unintentional. The English versions of the
specifications linked above are the definitive versions.

## Community cookbook <a href="#community-cookbook" class="anchorClass"></a>

The [Cookbook](https://iiif.io/api/cookbook/ "IIIF Cookbook") gathers
together examples of how to create <span class="abbr"
title="International Image Interoperability Framework">IIIF</span>
Presentation <span class="abbr"
title="Application Programming Interface">API</span> assets, in order
to:

- Provide many more examples than the specification alone can do, for
  reference and learning;
- Encourage publishers to adopt common patterns in modeling classes of
  complex objects;
- Enable client software developers to support these patterns, for
  consistency of user experience (when desirable); and
- Demonstrate the applicability of <span class="abbr"
  title="International Image Interoperability Framework">IIIF</span> to
  a broad range of use cases.

The [Cookbook](https://iiif.io/api/cookbook/ "IIIF Cookbook") webpages
are under constant development and the list of recipes include links to
completed recipes and place holders for future recipes. The community
welcomes additions to the
[Cookbook](https://iiif.io/api/cookbook/ "IIIF Cookbook"). To get
started, review the [Cookbook
process](https://iiif.io/api/cookbook/recipe/ "Cookbook process") and
say hello on the Cookbook [Slack](http://bit.ly/iiif-slack) channel.

## Validators <a href="#validators" class="anchorClass"></a>

- [Image <span class="abbr"
  title="Application Programming Interface">API</span>
  validator](/api/image/validator/) - A service to validate a
  <span class="abbr"
  title="International Image Interoperability Framework">IIIF</span>
  Image <span class="abbr"
  title="Application Programming Interface">API</span> resource against
  the specification.
- [Presentation <span class="abbr"
  title="Application Programming Interface">API</span>
  validator](/api/presentation/validator/service/) - A service to
  validate a <span class="abbr"
  title="International Image Interoperability Framework">IIIF</span>
  Presentation <span class="abbr"
  title="Application Programming Interface">API</span> resource against
  the specification.

## Older versions <a href="#older-versions" class="anchorClass"></a>

Current <span class="abbr"
title="International Image Interoperability Framework">IIIF</span>
specifications *should* be used for all new work. Old versions are
retained for reference and are listed below. Technical resources and
reference implementations of older versions are *NOT* guaranteed to be
maintained across new major versions.

| Old <span class="abbr" title="Application Programming Interface">API</span> Version | Notes |
|----|----|
| [Authentication <span class="abbr" title="Application Programming Interface">API</span> 0.9.4](/api/auth/0.9/ "Authentication API v0.9.4") | Published 2016-10-05 |
| [Authentication <span class="abbr" title="Application Programming Interface">API</span> 1.0](/api/auth/1.0/ "IIIF Authentication API 1.0") | Published 2017-01-19 |
| [Change Discovery <span class="abbr" title="Application Programming Interface">API</span> 0.9.2](/api/discovery/0.9/ "IIIF Change Discovery API") | Published 2021-04-28 |
| [Image <span class="abbr" title="Application Programming Interface">API</span> 2.1](/api/image/2.1/ "Image API 2.1") | Published 2016-05-12, updated 2017-06-09 |
| [Image <span class="abbr" title="Application Programming Interface">API</span> 2.0](/api/image/2.0/ "Image API v2.0") | Published 2014-09-11 |
| [Image <span class="abbr" title="Application Programming Interface">API</span> 1.1](/api/image/1.1/ "Image API 1.1") | Published 2013-09-17 |
| [Image <span class="abbr" title="Application Programming Interface">API</span> 1.0](/api/image/1.0/ "Image API v1.0") | Published 2012-08-10 |
| [Presentation <span class="abbr" title="Application Programming Interface">API</span> 2.1](/api/presentation/2.1/ "IIIF Presentation API 2.1") | Published 2016-05-12, updated 2017-06-09 |
| [Presentation <span class="abbr" title="Application Programming Interface">API</span> 2.0](/api/presentation/2.0/ "IIIF Presentation API 2.0") | Published 2014-08-12 |
| [Metadata <span class="abbr" title="Application Programming Interface">API</span> 1.0](/api/metadata/1.0/ "Metadata API v1.0") | “Metadata <span class="abbr" title="Application Programming Interface">API</span>” was replaced with the Presentation <span class="abbr" title="Application Programming Interface">API</span>, published 2013-09-16 |
| [Metadata <span class="abbr" title="Application Programming Interface">API</span> 0.9](/api/metadata/0.9/ "Metadata API v0.9") | Draft of the “Metadata <span class="abbr" title="Application Programming Interface">API</span>”, published 2013-06-11 |
| [Search <span class="abbr" title="Application Programming Interface">API</span> 0.9](/api/search/0.9/ "Search API v0.9") | Draft published 2016-04-11 |
| [Search <span class="abbr" title="Application Programming Interface">API</span> 1.0](/api/search/1.0/) | Published 2016-05-12 |

## Notes <a href="#notes" class="anchorClass"></a>

<span class="abbr"
title="International Image Interoperability Framework">IIIF</span> also
has a series of [Implementation
Notes](/api/annex/ "Implementation Notes") which are not subject to the
same process as formal APIs but may be useful to implementers.

## Process <a href="#process" class="anchorClass"></a>

<span class="abbr"
title="International Image Interoperability Framework">IIIF</span>
Specifications are created and published following the
[<span class="abbr"
title="International Image Interoperability Framework">IIIF</span>
Editorial
Process](https://iiif.io/community/policy/editorial/ "IIIF Editorial Process").

</div>

</div>

</div>

</div>

<div class="container">

<div class="columns">

<div class="navbar-brand column is-half">

<a href="/api/" class="navbar-item"><img
src="/api/assets/images/logos/logo-sm.png" height="28"
alt="IIIF logo" /> <span class="brand-title blue-text">International
Image Interoperability Framework</span></a>

IIIF is a set of open standards for delivering high-quality, attributed
digital objects online at scale. It’s also an international community
developing and implementing the IIIF APIs. IIIF is backed by a
consortium of leading cultural institutions.

</div>

<div class="column">

</div>

<div class="column menu-column">

#### About

- [How IIIF Works](https://iiif.io/get-started/how-iiif-works)
- [APIs & Documentation](/api)
- [Demos](https://iiif.io/demos)
- [Tutorials & Guides](https://iiif.io/guides)
- [Privacy policy](https://iiif.io/privacy)

</div>

<div class="column menu-column">

#### Stay Connected

- [News & Events](https://iiif.io/news-and-events)
- [Join Newsletter](https://iiif.io/newsletter)
- [Community Groups](https://iiif.io/community/groups)
- [Consortium](https://iiif.io/community/consortium)
- [Contact Us](https://iiif.io/contact)

</div>

</div>

</div>
