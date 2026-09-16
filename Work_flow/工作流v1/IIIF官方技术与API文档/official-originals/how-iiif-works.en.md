<div class="section hero is-primary"
style="background-image: linear-gradient(to bottom, rgba(0, 25, 39, 0.68), rgba(0, 25, 39, 0.68)), url('/assets/images/heroes/hero-2@3x.webp');
  background-size: cover;
  background-position: bottom center;
  background-attachment: fixed;
  ">

<div class="hero-head">

<div class="container">

<div class="navbar-brand">

<a href="/" class="navbar-item"><img
src="/assets/images/logos/logo-sm.png" height="28" alt="IIIF logo" />
<span class="brand-title">International Image Interoperability
Framework</span></a>

<div class="navbar-burger" data-target="navbar"
onclick="document.querySelector('.navbar-menu').classList.toggle('is-active');">

</div>

</div>

<div class="navbar-menu">

<div class="navbar-end">

<a href="/" class="navbar-item">Home</a>
<a href="/demos" class="navbar-item">Demos</a>
<a href="/events" class="navbar-item">Events</a>
<a href="/news" class="navbar-item">News</a>

<div class="navbar-item has-dropdown is-hoverable">

<a href="/get-involved" class="navbar-link">Get Involved</a>

<div class="navbar-dropdown is-boxed is-active">

<a href="/community/" class="navbar-item">Community</a>
<a href="/community/consortium" class="navbar-item">Consortium</a>
<a href="/newsletter" class="navbar-item">Join Newsletter</a>
<a href="/get-involved/outreach-materials" class="navbar-item">Outreach
Materials</a> <a href="/community/consortium/strategic_plan_26-28"
class="navbar-item">Strategic Plan</a>

</div>

</div>

<div class="navbar-item has-dropdown is-hoverable">

<a href="/get-started" class="navbar-link">Get Started</a>

<div class="navbar-dropdown is-boxed is-active">

<a href="/get-started/how-iiif-works" class="navbar-item">How IIIF
Works</a> <a href="/community/ambassadors/" class="navbar-item">IIIF
Ambassadors</a>
<a href="https://iiif.io/guides" class="navbar-item">Guides</a>
<a href="https://iiif.io/api" class="navbar-item">APIs &amp;
Documentation</a>
<a href="/get-started/cookbook" class="navbar-item">Cookbooks</a>
<a href="/get-started/training" class="navbar-item">Training</a>

</div>

</div>

</div>

</div>

</div>

</div>

<div class="hero-body container">

- [Get Started](/get-started/)

<div class="container has-text-centered">

# How It Works

A plain-language guide to how the APIs work.

</div>

</div>

</div>

<div id="main" class="section">

<div class="container-block is-max-widescreen">

<div class="container">

<div class="content">

## Introduction

Learning about IIIF (generally pronounced “triple-eye-eff”) can be
overwhelming at first, especially if you’re not a programmer, so we’ve
created a plain-language guide for newcomers. We’ve also created a
glossary of [“Key concepts you’ll encounter when working with
IIIF”](/get-started/how-iiif-works/#key-concepts-youll-encounter-when-working-with-iiif)
which you’ll find at the end of this page.

As you are learning, please know that the community is here to help.
Feel free to reach out on [Slack](http://bit.ly/iiif-slack) or our email
discussion list
([iiif-discuss](https://groups.google.com/forum/#!forum/iiif-discuss))
with any questions. There’s also a [self-paced online
tutorial](https://training.iiif.io/iiif-online-workshop/) that may be a
useful next step for newcomers, or check out our general set of
resources for [getting started with IIIF](/get-started/).

<div class="container mgt-medium mgb-medium">

[![delivery
diagram](/assets/images/zeplin/delivery@3x.png)](/assets/images/zeplin/delivery@3x.png)
<span class="caption">A diagram of how the core IIIF APIs work
together.</span>

</div>

## The basics

IIIF is a way to standardize the delivery of images and audio/visual
files from servers to different environments on the Web where they can
then be viewed and interacted with in many ways.

Modern Web browsers understand how to display formats like .jpg and .mp4
at defined sizes, but cannot do much else. The IIIF specifications align
with general Web standards that define how all browsers work to enable
richer functionality beyond viewing an image or audio/visual files. For
images, that means enabling deep zoom, comparison, structure (i.e., for
an object such as a book, structure = page order) and annotation. For
audio/visual materials, that means being able to deliver complex
structures (such as several reels of film that make up a single movie)
along with things like captions, transcriptions/translations,
annotations, and more.

IIIF makes these objects work in a consistent way. That enables
portability across viewers, the ability to connect and unite materials
across institutional boundaries, and more.

## The Image and Presentation APIs

There are two main components to IIIF: delivering digital objects to
sites and viewing them.

### Delivering objects

The Image API defines how image servers deliver image pixels to a
viewer. It allows the image to be sent as a full-sized image or as a
smaller size, a zoomed portion, a rotated view, or as a black and white
version. All of these settings are designated by changing portions of
the URL for an Image API resource. To try it out for yourself, head over
to this [Image API
Playrground](https://www.learniiif.org/image-api/playground) and adjust
some of the Image API parameters to see how they work with real images.

The Image API can be implemented on its own (most commonly to enable
fast, deep zoom of very high resolution files like TIF and JP2000), or
alongside the Presentation API for additional viewing capabilities.

<div class="container mgt-medium mgb-medium">

[![Image API
filler](https://iiif.io/api/image/1.0/images/iiif-order.png)](https://iiif.io/api/image/1.0/images/iiif-order.png)
<span class="caption">The image API controls the form in which an image
is delivered to a location on the Web.</span>

</div>

### Viewing objects

The Presentation API attaches basic metadata and structure to digital
objects, defining how they appear in viewers. It does this via the
Manifest, a JSON file which bundles up all the different elements of an
IIIF object (such as a single image, or a series of images) with basic
metadata (like title, description, and rights information) and
structural information (such as page order). ([See the glossary
below](/get-started/how-iiif-works/#key-concepts-youll-encounter-when-working-with-iiif)
for more definitions of common IIIF terms.)

<figure class="image inline-image float-right">
<img src="/assets/uploads/presentation-api-filler.png"
alt="API filler image" />
<figcaption>The presentation API delivers data and structure about an
image to a viewer.</figcaption>
</figure>

There are many [IIIF viewers](/get-started/iiif-viewers/). Some are
general purpose tools while others specialize in particular kinds of
content or functionality. IIIF-compatible viewers generally allow users
to pan, zoom, rotate, and resize image objects, and play audio/visual
files. Some allow annotation with text, audio, location, and more.
Others allow comparison of objects from a single collection side-by-side
(or even objects from multiple collections if the object’s Manifest is
made available to users).

## Advanced use cases

IIIF also enables you to use the same standardized principles to manage
other needs related to your IIIF objects.

- **Authentication**: The Authentication API defines where or by who
  your objects can be viewed.
- **Search**: The Search API allows users to search within any text
  associated with an object (such as OCR, transcriptions, etc.)
- **Content state**: The Content State API provides a way of linking
  directly to a particular region and zoom level of a IIIF resource.
- **Change discovery**: The Change Discovery API is a tool to describe
  the new publication of and updates to digital objects, to help aid
  cross-institutional discovery.

## Putting it all together

If you have your own images you want to put online using IIIF you’ll
need high-quality assets (most people use JPEG2000 or TIF files), and
metadata about structure as well as the information people will read
about the image.

From there:

- Make images and audio/video materials available using the Image API
  and an [IIIF image server](/get-started/image-servers/), or a
  [IIIF-compatible image server from a vendor or other web
  host](/get-started/vendors/).
- Combine your images and structural data (like pagination or ordering)
  from your metadata source into a IIIF Manifest using the Presentation
  API (there are many [open source or vendor products that help handle
  this](https://github.com/IIIF/awesome-iiif#presentation-api-libraries)).
- Choose a [viewer](/get-started/iiif-viewers/) to show your images
- Consider making your image **manifests** (definition below) available
  publicly on your collection site so users can work with your images
  across collections.

</div>

</div>

</div>

<div class="container-block is-max-widescreen">

<div class="container has-text-centered">

## Next steps

Feel like you have a handle on the basics? Try out some of these
resources as a next step, or see our “Get Started” page for the full set
of ways to get started with IIIF.

<div class="block columns is-multiline">

<div class="column is-one-third same-height-column">

<div class="box hover-box iiif-card">

### Get started

Take the first step to exploring the rich world of IIIF-enabled
materials.

[Learn more \>](/get-started/)

</div>

</div>

<div class="column is-one-third same-height-column">

<div class="box hover-box iiif-card">

### Guides

A set of resources to help you find and work with IIIF materials, built
by members of the IIIF community.

[Learn more \>](https://iiif.io/guides)

</div>

</div>

<div class="column is-one-third same-height-column">

<div class="box hover-box iiif-card">

### Talks

Watch selected talks from conferences and other events to learn more
about IIIF directly from the community.

[Learn more \>](/get-started/talks)

</div>

</div>

</div>

</div>

</div>

<div class="container-block is-max-widescreen">

<div class="container has-text-centered">

## Key concepts you’ll encounter when working with IIIF

<div class="has-text-justified">

**Annotation:** a standard way to associate different types of content
to whatever is on your canvas (such as a translation of a line or the
name of a person in a photograph. In the IIIF model, images and other
presentation content are also technically annotations onto a canvas).
For more detail, see the [Web Annotation Data
Model](http://w3.org/TR/annotation-model/).

**Canvas:** the frame of reference for the display of your content, both
spatial and temporal (just like a painting canvas for two-dimensional
materials, or with an added time dimension for a/v content).

**Collection:** a set of manifests (or ‘child’ collections) that
communicate hierarchy or gather related things (for example, a set of
boxes that each have folders within them, and photographs within those
folders).

**Image server:** the computer or service where digital objects live
(basically, where assets are stored while waiting for users to access
them).

**Image viewer:** software, usually web-based, that allows viewing and
manipulation of images. Sometimes called a “client.” (This is almost
always the tool via which end users interact with IIIF materials, and
many image viewers add additional functionality like the ability to add
annotations or search through transcriptions/translations, etc.)

**Manifest:** the prime unit in IIIF which lists all the information
that makes up a IIIF object. It communicates how to display your digital
objects, and what information to display about them, including
structure, to varying degrees of complexity as determined by the
implementer. (For example, if the object is a book of illustrations,
where each illustrated page is a canvas, and there is one specific order
to the arrangement of those pages).

**Metadata source:** the place where the information about objects live,
and needs to be connected to your Manifest via the Presentation API (for
libraries and museums, this is usually some kind of asset management
system, though there are many other possibilities)

**Range:** a particular order of Canvases (as a basic example, think of
the order of pages in a book, or the order of tracks on a music album)

</div>

</div>

</div>

</div>

<div class="container">

<div class="columns">

<div class="navbar-brand column is-half">

<a href="/" class="navbar-item"><img
src="/assets/images/logos/logo-sm.png" height="28" alt="IIIF logo" />
<span class="brand-title blue-text">International Image Interoperability
Framework</span></a>

IIIF is a set of open standards for delivering high-quality, attributed
digital objects online at scale. It’s also an international community
developing and implementing the IIIF APIs. IIIF is backed by a
consortium of leading cultural institutions.

</div>

<div class="column">

</div>

<div class="column menu-column">

#### About

- [How IIIF Works](/get-started/how-iiif-works)
- [APIs & Documentation](https://iiif.io/api)
- [Demos](/demos)
- [Tutorials & Guides](https://iiif.io/guides)
- [Privacy policy](/privacy)

</div>

<div class="column menu-column">

#### Stay Connected

- [News & Events](/news-and-events)
- [Join Newsletter](/newsletter)
- [Community Groups](/community/groups)
- [Consortium](/community/consortium)
- [Contact Us](/contact)

</div>

</div>

</div>
