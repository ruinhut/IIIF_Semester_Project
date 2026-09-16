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

# Presentation API 3.0

</div>

</div>

</div>

<div id="main" class="section">

<div class="container-block no-padding is-max-desktop">

<div class="columns is-max-desktop">

<div class="aside column is-one-quarter api-sidebar-container"
data-markdown="1">

<div class="toc-sidebar sticky">

- [1. Introduction](#1-introduction)
  - [1.1. Objectives and Scope](#11-objectives-and-scope)
  - [1.2. Terminology](#12-terminology)
- [2. Resource Type Overview](#2-resource-type-overview)
  - [2.1. Defined Types](#21-defined-types)
  - [2.2. Additional Types](#22-additional-types)
- [3. Resource Properties](#3-resource-properties)
  - [3.1. Descriptive Properties](#31-descriptive-properties)
  - [3.2. Technical Properties](#32-technical-properties)
  - [3.3. Linking Properties](#33-linking-properties)
  - [3.4. Structural Properties](#34-structural-properties)
  - [3.5. Values](#35-values)
- [4. <span class="abbr" title="JSON for Linking Data">JSON-LD</span>
  Considerations](#4-json-ld-considerations)
  - [4.1. Case Sensitivity](#41-case-sensitivity)
  - [4.2. Resource Representations](#42-resource-representations)
  - [4.3. Properties with Multiple
    Values](#43-properties-with-multiple-values)
  - [4.4. Language of Property Values](#language-of-property-values)
  - [4.5. <span class="abbr"
    title="HyperText Markup Language">HTML</span> Markup in Property
    Values](#45-html-markup-in-property-values)
  - [4.6. Linked Data Context and
    Extensions](#46-linked-data-context-and-extensions)
  - [4.7. Term Collisions between
    Contexts](#47-term-collisions-between-contexts)
  - [4.8. Keyword Mappings](#48-keyword-mappings)
- [5. Resource Structure](#5-resource-structure)
  - [5.1. Collection](#51-collection)
  - [5.2. Manifest](#52-manifest)
  - [5.3. Canvas](#53-canvas)
  - [5.4. Range](#54-range)
  - [5.5. Annotation Page](#55-annotation-page)
  - [5.6. Annotation](#56-annotation)
  - [5.7. Content Resources](#57-content-resources)
  - [5.8. Annotation Collection](#58-annotation-collection)
- [6. <span class="abbr" title="Hypertext Transfer Protocol">HTTP</span>
  Requests and Responses](#6-http-requests-and-responses)
  - [6.1. URI Recommendations](#61-uri-recommendations)
  - [6.2. Requests](#62-requests)
  - [6.3. Responses](#63-responses)
- [7. Authentication](#7-authentication)
- [Appendices](#appendices)
  - [A. Summary of Property
    Requirements](#a-summary-of-property-requirements)
  - [B. Example Manifest Response](#b-example-manifest-response)
  - [C. Versioning](#c-versioning)
  - [D. Acknowledgements](#d-acknowledgements)
  - [E. Change Log](#e-change-log)

</div>

</div>

<div class="column is-three-quarters content api-content"
data-markdown="1">

## Status of this Document <a href="#status-of-this-document" class="anchorClass"></a>

**This Version:** 3.0.0

**Latest Stable Version:**
[3.0.0](/api/presentation/3.0/ "Latest Presentation API Stable Version")

**Previous Version:**
[2.1.1](/api/presentation/2.1/ "IIIF Presentation API 2.1")

**Editors:**

- **[Michael Appleby](https://orcid.org/0000-0002-1266-298X)**, Yale
  University

- **[Tom Crane](https://orcid.org/0000-0003-1881-243X)**, Digirati

- **[Robert Sanderson](https://orcid.org/0000-0003-4441-6852)**, J. Paul
  Getty Trust

- **[Jon Stroop](https://orcid.org/0000-0002-0367-1243)**, Princeton
  University Library

- **[Simeon Warner](https://orcid.org/0000-0002-7970-7855)**, Cornell
  University

*Copyright © 2012-2026 Editors and contributors. Published by the
<span class="abbr"
title="International Image Interoperability Framework">IIIF</span>
Consortium under the
[CC-BY](http://creativecommons.org/licenses/by/4.0/ "Creative Commons — Attribution 4.0 International")
license, see [disclaimer](/api/annex/notes/disclaimer/).*

------------------------------------------------------------------------

## 1. Introduction <a href="#1-introduction" class="anchorClass"></a>

Access to digital representations of objects is a fundamental
requirement for many research activities, for the transmission of
cultural knowledge, and for the daily pursuits of every web citizen.
Ancient scrolls, paintings, letters, books, newspapers, films, operas,
albums, field recordings, and computer generated animations are compound
objects: they can have many parts, and complex structures. These
resources may also bear the written or spoken word, and this linguistic
content is often as important as the visual or audible representation.

Collections of both digitized physical objects and much born-digital
content benefit from a standardized description of their structure,
layout, and presentation mode. This document specifies this standardized
description of the collection or compound object, using a
<span class="abbr" title="JavaScript Object Notation">JSON</span>
format. Many different rich and dynamic user experiences can be
implemented, presenting content from across collections and
institutions.

A compound object may comprise a series of pages, surfaces, or extents
of time; for example the single view of a painting, the two sides of a
photograph, four cardinal views of a statue, the many pages of an
edition of a newspaper or book, or the duration of an act of an opera.
This specification addresses how to provide an order for these views or
extents, the references to the resources needed to present them, and the
descriptive information needed to allow the user to understand what is
being seen or heard.

The principles of [Linked Data](http://linkeddata.org/ "Linked Data")
and the [Architecture of the
Web](http://www.w3.org/TR/webarch/ "Architecture of the World Wide Web")
are adopted in order to provide a distributed and interoperable
framework. The [Shared Canvas data
model](/api/model/shared-canvas/1.0/ "Shared Canvas Data Model") and
[<span class="abbr"
title="JSON for Linking Data">JSON-LD</span>](https://www.w3.org/TR/json-ld/ "JSON-LD 1.0")
are leveraged to create an easy-to-implement, <span class="abbr"
title="JavaScript Object Notation">JSON</span>-based format.

Please send feedback to <iiif-discuss@googlegroups.com>

### 1.1. Objectives and Scope <a href="#11-objectives-and-scope" class="anchorClass"></a>

The objective of the <span class="abbr"
title="International Image Interoperability Framework">IIIF</span>
(pronounced “Triple-Eye-Eff”) Presentation <span class="abbr"
title="Application Programming Interface">API</span> is to provide the
information necessary to allow a rich, online viewing environment for
compound digital objects to be presented to a human user, often in
conjunction with the [<span class="abbr"
title="International Image Interoperability Framework">IIIF</span> Image
<span class="abbr"
title="Application Programming Interface">API</span>](/api/image/3.0/ "Image API").
This is the sole purpose of the <span class="abbr"
title="Application Programming Interface">API</span> and therefore
descriptive information is given in a way that is intended for humans to
read, but not semantically available to machines. In particular, it
explicitly does **not** aim to provide metadata that would allow a
search engine to index digital objects.

Implementations of this specification will be able to:

- display to the user digitized images, video, audio, and other content
  types associated with a particular physical or born-digital object;
- allow the user to navigate between multiple views or time extents of
  the object, either sequentially or hierarchically;
- display descriptive information about the object, view or navigation
  structure to provide context to the user;
- and provide a shared environment in which both publishers and users
  can annotate the object and its content with additional information.

The following are **not** in scope:

- Provision of metadata for harvesting and discovery is not directly
  supported. Properties to reference further descriptive resources are
  available, and their use is encouraged.
- Search within the object, which is described by the
  [<span class="abbr"
  title="International Image Interoperability Framework">IIIF</span>
  Content Search <span class="abbr"
  title="Application Programming Interface">API</span>](/api/search/2.0/ "Content Search API").

This document is accompanied by the [Presentation <span class="abbr"
title="Application Programming Interface">API</span>
Cookbook](https://iiif.io/api/cookbook/ "IIIF Cookbook"), which
demonstrates motivating use cases for <span class="abbr"
title="International Image Interoperability Framework">IIIF</span> and
contains examples showing how the objectives may be achieved.

### 1.2. Terminology <a href="#12-terminology" class="anchorClass"></a>

This specification uses the following terms:

- **embedded**: When a resource (A) is embedded within an embedding
  resource (B), the complete <span class="abbr"
  title="JavaScript Object Notation">JSON</span> representation of
  resource A is present within the <span class="abbr"
  title="JavaScript Object Notation">JSON</span> representation of
  resource B, and dereferencing the URI of resource A will not result in
  additional information. Example: Canvas A is embedded in Manifest B.
- **referenced**: When a resource (A) is referenced from a referencing
  resource (B), an incomplete <span class="abbr"
  title="JavaScript Object Notation">JSON</span> representation of
  resource A is present within the <span class="abbr"
  title="JavaScript Object Notation">JSON</span> representation of
  resource B, and dereferencing the URI of resource A will result in
  additional information. Example: Manifest A is referenced from
  Collection B.
- **<span class="abbr"
  title="Hypertext Transfer Protocol">HTTP</span>(S)**: The
  <span class="abbr" title="Hypertext Transfer Protocol">HTTP</span> or
  <span class="abbr"
  title="Hypertext Transfer Protocol (Secure)">HTTPS</span> URI scheme
  and internet protocol.

The terms *array*, *<span class="abbr"
title="JavaScript Object Notation">JSON</span> object*, *number*,
*string*, and *boolean* in this document are to be interpreted as
defined by the [Javascript Object Notation (<span class="abbr"
title="JavaScript Object Notation">JSON</span>)](https://tools.ietf.org/html/rfc8259 "JSON RFC")
specification.

The key words *must*, *must not*, *required*, *shall*, *shall not*,
*should*, *should not*, *recommended*, *may*, and *optional* in this
document are to be interpreted as described in [<span class="abbr"
title="Request for Comments">RFC</span>
2119](https://tools.ietf.org/html/rfc2119 "RFC Keywords").

## 2. Resource Type Overview <a href="#2-resource-type-overview" class="anchorClass"></a>

The objectives described above require a model in which one can
characterize the compound object (via the *Manifest* resource) and the
individual views of the object (*Canvas* resources). Each view may
reference images, audio, video and other content resources to allow it
to be rendered appropriately. A compound object may also have sections;
for example, a book may have chapters of several pages, or a play might
be divided into acts and scenes (*Range* resources) and there may be
groups of such objects (*Collection* resources). These resource types,
along with their properties, make up the <span class="abbr"
title="International Image Interoperability Framework">IIIF</span>
Presentation <span class="abbr"
title="Application Programming Interface">API</span>.

This section provides an overview of the resource types (or classes)
that are used in the specification. They are each presented in more
detail in [Section 5](/api/presentation/3.0/#5-resource-structure).

### 2.1. Defined Types <a href="#21-defined-types" class="anchorClass"></a>

This specification defines the following resource types:

<img src="/api/assets/images/data-model.png" width="400"
alt="Data Model" />\

##### Collection <a href="#overview-collection" class="anchorClass"></a>

An ordered list of Manifests, and/or further Collections. Collections
allow Manifests and child Collections to be grouped in a hierarchical
structure for presentation, which can be for generating navigation,
showing dynamic results from a search, or providing fixed sets of
related resources for any other purpose.

##### Manifest <a href="#overview-manifest" class="anchorClass"></a>

A description of the structure and properties of the compound object. It
carries information needed for the client to present the content to the
user, such as a title and other descriptive information about the object
or the intellectual work that it conveys. Each Manifest usually
describes how to present a single compound object such as a book, a
statue or a music album.

##### Canvas <a href="#overview-canvas" class="anchorClass"></a>

A virtual container that represents a particular view of the object and
has content resources associated with it or with parts of it. The Canvas
provides a frame of reference for the layout of the content, both
spatially and temporally. The concept of a Canvas is borrowed from
standards like PDF and <span class="abbr"
title="HyperText Markup Language">HTML</span>, or applications like
Photoshop and PowerPoint, where an initially blank display surface has
images, video, text and other content “painted” on to it by Annotations,
collected in Annotation Pages.

##### Range <a href="#overview-range" class="anchorClass"></a>

An ordered list of Canvases, and/or further Ranges. Ranges allow
Canvases, or parts thereof, to be grouped together in some way. This
could be for content-based reasons, such as might be described in a
table of contents or the set of scenes in a play. Equally, physical
features might be important such as page gatherings in an early book, or
when recorded music is split across different physical carriers such as
two CDs.

### 2.2. Additional Types <a href="#22-additional-types" class="anchorClass"></a>

This specification makes use of types defined in the [Web Annotation
Data Model](http://w3.org/TR/annotation-model/ "Web Annotation Model")
specification, in particular the following:

##### Annotation Page <a href="#overview-annotationpage" class="anchorClass"></a>

An ordered list of Annotations that is typically associated with a
Canvas but may be referenced from other types of resource as well.
Annotation Pages collect and order lists of Annotations, which in turn
provide commentary about a resource or content that is part of a Canvas.

##### Annotation <a href="#overview-annotation" class="anchorClass"></a>

Annotations associate content resources with Canvases. The same
mechanism is used for the visible and/or audible resources as is used
for transcriptions, commentary, tags and other content. This provides a
single, unified method for aligning information, and provides a
standards-based framework for distinguishing parts of resources and
parts of Canvases. As Annotations can be added later, it promotes a
distributed system in which publishers can align their content with the
descriptions created by others. Annotation related functionality may
also rely on further classes such as SpecificResource, Choice or
Selectors.

##### Content <a href="#overview-content" class="anchorClass"></a>

Web resources such as images, audio, video, or text which are associated
with a Canvas via an Annotation, or provide a representation of any
resource.

##### Annotation Collection <a href="#overview-annotationcollection" class="anchorClass"></a>

An ordered list of Annotation Pages. Annotation Collections allow higher
level groupings of Annotations to be recorded. For example, all of the
English translation Annotations of a medieval French document could be
kept separate from the transcription or an edition in modern French, or
the director’s commentary on a film can be separated from the script.

## 3. Resource Properties <a href="#3-resource-properties" class="anchorClass"></a>

Most of the properties defined by this specification may be associated
with any of the resource types described above, and may have more than
one value. Properties relate to the resource with which they are
associated, so the `label` property on a Manifest is the human readable
label of the Manifest, whereas the same `label` property on a Canvas is
the human readable label for that particular view.

The requirements for which classes have which properties are summarized
in [Appendix
A](/api/presentation/3.0/#a-summary-of-property-requirements).

Other properties are allowed, either via local extensions or those
endorsed by the <span class="abbr"
title="International Image Interoperability Framework">IIIF</span>
community. If a client discovers properties that it does not understand,
then it *must* ignore them. See the [Linked Data Context and
Extensions](/api/presentation/3.0/#46-linked-data-context-and-extensions "Linked Data Context and Extensions")
section for more information about extensions.

This section also defines processing requirements for clients for each
of the combinations of class and property. These requirements are for
general purpose client implementations that are intended to be used to
render the entire resource to the user, and not necessarily for
consuming applications with specialized use or individual component
implementations that might be used to construct a client. The inclusion
of these requirements gives publishers a baseline expectation for how
they can expect implementations advertised as compliant with this
specification to behave when processing their content.

### 3.1. Descriptive Properties <a href="#31-descriptive-properties" class="anchorClass"></a>

These properties describe or represent the resource they are associated
with, and are typically rendered to the user.

##### label <a href="#label" class="anchorClass"></a>

A human readable label, name or title. The `label` property is intended
to be displayed as a short, textual surrogate for the resource if a
human needs to make a distinction between it and similar resources, for
example between objects, pages, or options for a choice of images to
display. The `label` property can be fully internationalized, and each
language can have multiple values. This pattern is described in more
detail in the
[languages](/api/presentation/3.0/#language-of-property-values "Language of Property Values")
section.

The value of the property *must* be a <span class="abbr"
title="JavaScript Object Notation">JSON</span> object, as described in
the
[languages](/api/presentation/3.0/#language-of-property-values "Language of Property Values")
section.

- A Collection *must* have the `label` property with at least one
  entry.\
  Clients *must* render `label` on a Collection.
- A Manifest *must* have the `label` property with at least one entry.\
  Clients *must* render `label` on a Manifest.
- A Canvas *should* have the `label` property with at least one entry.\
  Clients *must* render `label` on a Canvas, and *should* generate a
  `label` for Canvases that do not have them.
- A content resource *may* have the `label` property with at least one
  entry. If there is a Choice of content resource for the same Canvas,
  then they *should* each have at least the `label` property with at
  least one entry.\
  Clients *may* render `label` on content resources, and *should* render
  them when part of a Choice.
- A Range *should* have the `label` property with at least one entry.\
  Clients *must* render `label` on a Range.
- An Annotation Collection *should* have the `label` property with at
  least one entry.\
  Clients *should* render `label` on an Annotation Collection.
- Other types of resource *may* have the `label` property with at least
  one entry.\
  Clients *may* render `label` on other types of resource.

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{ "label": { "en": [ "Example Object Title" ] } }
```

</div>

</div>

##### metadata <a href="#metadata" class="anchorClass"></a>

An ordered list of descriptions to be displayed to the user when they
interact with the resource, given as pairs of human readable `label` and
`value` entries. The content of these entries is intended for
presentation only; descriptive semantics *should not* be inferred. An
entry might be used to convey information about the creation of the
object, a physical description, ownership information, or other
purposes.

The value of the `metadata` property *must* be an array of
<span class="abbr" title="JavaScript Object Notation">JSON</span>
objects, where each item in the array has both `label` and `value`
properties. The values of both `label` and `value` *must* be
<span class="abbr" title="JavaScript Object Notation">JSON</span>
objects, as described in the
[languages](/api/presentation/3.0/#language-of-property-values "Language of Property Values")
section.

- A Collection *should* have the `metadata` property with at least one
  item.\
  Clients *must* render `metadata` on a Collection.
- A Manifest *should* have the `metadata` property with at least one
  item.\
  Clients *must* render `metadata` on a Manifest.
- A Canvas *may* have the `metadata` property with at least one item.\
  Clients *should* render `metadata` on a Canvas.
- Other types of resource *may* have the `metadata` property with at
  least one item.\
  Clients *may* render `metadata` on other types of resource.

Clients *should* display the entries in the order provided. Clients
*should* expect to encounter long texts in the `value` property, and
render them appropriately, such as with an expand button, or in a tabbed
interface.

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "metadata": [
    {
      "label": { "en": [ "Creator" ] },
      "value": { "en": [ "Anne Artist (1776-1824)" ] }
    }
  ]
}
```

</div>

</div>

##### summary <a href="#summary" class="anchorClass"></a>

A short textual summary intended to be conveyed to the user when the
`metadata` entries for the resource are not being displayed. This could
be used as a brief description for item level search results, for
small-screen environments, or as an alternative user interface when the
`metadata` property is not currently being rendered. The `summary`
property follows the same pattern as the `label` property described
above.

The value of the property *must* be a <span class="abbr"
title="JavaScript Object Notation">JSON</span> object, as described in
the
[languages](/api/presentation/3.0/#language-of-property-values "Language of Property Values")
section.

- A Collection *should* have the `summary` property with at least one
  entry.\
  Clients *should* render `summary` on a Collection.
- A Manifest *should* have the `summary` property with at least one
  entry.\
  Clients *should* render `summary` on a Manifest.
- A Canvas *may* have the `summary` property with at least one entry.\
  Clients *should* render `summary` on a Canvas.
- Other types of resource *may* have the `summary` property with at
  least one entry.\
  Clients *may* render `summary` on other types of resource.

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{ "summary": { "en": [ "This is a summary of the object." ] } }
```

</div>

</div>

##### requiredStatement <a href="#requiredstatement" class="anchorClass"></a>

Text that *must* be displayed when the resource is displayed or used.
For example, the `requiredStatement` property could be used to present
copyright or ownership statements, an acknowledgement of the owning
and/or publishing institution, or any other text that the publishing
organization deems critical to display to the user. Given the wide
variation of potential client user interfaces, it will not always be
possible to display this statement to the user in the client’s initial
state. If initially hidden, clients *must* make the method of revealing
it as obvious as possible.

The value of the property *must* be a <span class="abbr"
title="JavaScript Object Notation">JSON</span> object, that has the
`label` and `value` properties, in the same way as a `metadata` property
entry. The values of both `label` and `value` *must* be
<span class="abbr" title="JavaScript Object Notation">JSON</span>
objects, as described in the
[languages](/api/presentation/3.0/#language-of-property-values "Language of Property Values")
section.

- Any resource type *may* have the `requiredStatement` property.\
  Clients *must* render `requiredStatement` on every resource type.

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "requiredStatement": {
    "label": { "en": [ "Attribution" ] },
    "value": { "en": [ "Provided courtesy of Example Institution" ] }
  }
}
```

</div>

</div>

##### rights <a href="#rights" class="anchorClass"></a>

A string that identifies a license or rights statement that applies to
the content of the resource, such as the <span class="abbr"
title="JavaScript Object Notation">JSON</span> of a Manifest or the
pixels of an image. The value *must* be drawn from the set of [Creative
Commons](https://creativecommons.org/licenses/ "Create Commons Licenses")
license URIs, the
[RightsStatements.org](http://rightsstatements.org/page/1.0/ "rightsstatements.org")
rights statement URIs, or those added via the
[extension](/api/presentation/3.0/#46-linked-data-context-and-extensions "Linked Data Context and Extensions")
mechanism. The inclusion of this property is informative, and for
example could be used to display an icon representing the rights
assertions.

If displaying rights information directly to the user is the desired
interaction, or a publisher-defined label is needed, then it is
*recommended* to include the information using the `requiredStatement`
property or in the `metadata` property.

The value *must* be a string. If the value is drawn from Creative
Commons or RightsStatements.org, then the string *must* be a URI defined
by that specification.

- Any resource type *may* have the `rights` property.\
  Clients *may* render `rights` on any resource type.

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{ "rights": "http://creativecommons.org/licenses/by/4.0/" }
```

</div>

</div>

**Machine actionable URIs and links for users**\
The machine actionable URIs for both Creative Commons licenses and
RightsStatements.org right statements are `http` URIs. In both cases,
human readable descriptions are available from equivalent `https` URIs.
Clients may wish to rewrite links presented to users to use these
equivalent `https` URIs.

##### provider <a href="#provider" class="anchorClass"></a>

An organization or person that contributed to providing the content of
the resource. Clients can then display this information to the user to
acknowledge the provider’s contributions. This differs from the
`requiredStatement` property, in that the data is structured, allowing
the client to do more than just present text but instead have richer
information about the people and organizations to use in different
interfaces.

The organization or person is represented as an `Agent` resource.

- Agents *must* have the `id` property, and its value *must* be a
  string. The string *must* be a URI that identifies the agent.
- Agents *must* have the `type` property, and its value *must* be the
  string “Agent”.
- Agents *must* have the `label` property, and its value *must* be a
  <span class="abbr" title="JavaScript Object Notation">JSON</span>
  object as described in the
  [languages](/api/presentation/3.0/#language-of-property-values "Language of Property Values")
  section.
- Agents *should* have the `homepage` property, and its value *must* be
  an array of <span class="abbr"
  title="JavaScript Object Notation">JSON</span> objects as described in
  the [homepage](/api/presentation/3.0/#homepage "homepage property")
  section.
- Agents *should* have the `logo` property, and its value *must* be an
  array of <span class="abbr"
  title="JavaScript Object Notation">JSON</span> objects as described in
  the [logo](/api/presentation/3.0/#logo "logo property") section.
- Agents *may* have the `seeAlso` property, and its value *must* be an
  array of <span class="abbr"
  title="JavaScript Object Notation">JSON</span> object as described in
  the [seeAlso](/api/presentation/3.0/#seealso "seeAlso property")
  section.

The value *must* be an array of <span class="abbr"
title="JavaScript Object Notation">JSON</span> objects, where each item
in the array conforms to the structure of an Agent, as described above.

- A Collection *should* have the `provider` property with at least one
  item.\
  Clients *must* render `provider` on a Collection.
- A Manifest *should* have the `provider` property with at least one
  item.\
  Clients *must* render `provider` on a Manifest.
- Other types of resource *may* have the `provider` property with at
  least one item.\
  Clients *should* render `provider` on other types of resource.

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "provider": [
    {
      "id": "https://example.org/about",
      "type": "Agent",
      "label": { "en": [ "Example Organization" ] },
      "homepage": [
        {
          "id": "https://example.org/",
          "type": "Text",
          "label": { "en": [ "Example Organization Homepage" ] },
          "format": "text/html"
        }
      ],
      "logo": [
        {
          "id": "https://example.org/images/logo.png",
          "type": "Image",
          "format": "image/png",
          "height": 100,
          "width": 120
        }
      ],
      "seeAlso": [
        {
          "id": "https://data.example.org/about/us.jsonld",
          "type": "Dataset",
          "format": "application/ld+json",
          "profile": "https://schema.org/"
        }
      ]
    }
  ]
}
```

</div>

</div>

##### thumbnail <a href="#thumbnail" class="anchorClass"></a>

A content resource, such as a small image or short audio clip, that
represents the resource that has the `thumbnail` property. A resource
*may* have multiple thumbnail resources that have the same or different
`type` and `format`.

The value *must* be an array of <span class="abbr"
title="JavaScript Object Notation">JSON</span> objects, each of which
*must* have the `id` and `type` properties, and *should* have the
`format` property. Images and videos *should* have the `width` and
`height` properties, and time-based media *should* have the `duration`
property. It is *recommended* that a [<span class="abbr"
title="International Image Interoperability Framework">IIIF</span> Image
<span class="abbr"
title="Application Programming Interface">API</span>](/api/image/3.0/ "Image API")
service be available for images to enable manipulations such as
resizing.

- A Collection *should* have the `thumbnail` property with at least one
  item.\
  Clients *should* render `thumbnail` on a Collection.
- A Manifest *should* have the `thumbnail` property with at least one
  item.\
  Clients *should* render `thumbnail` on a Manifest.
- A Canvas *may* have the `thumbnail` property with at least one item. A
  Canvas *should* have the `thumbnail` property if there are multiple
  resources that make up the view.\
  Clients *should* render `thumbnail` on a Canvas.
- A content resource *may* have the `thumbnail` property with at least
  one item. Content resources *should* have the `thumbnail` property
  with at least one item if it is an option in a Choice of resources.\
  Clients *should* render `thumbnail` on a content resource.
- Other types of resource *may* have the `thumbnail` property with at
  least one item.\
  Clients *may* render `thumbnail` on other types of resource.

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "thumbnail": [
    {
      "id": "https://example.org/img/thumb.jpg",
      "type": "Image",
      "format": "image/jpeg",
      "width": 300,
      "height": 200
    }
  ]
}
```

</div>

</div>

##### navDate <a href="#navdate" class="anchorClass"></a>

A date that clients may use for navigation purposes when presenting the
resource to the user in a date-based user interface, such as a calendar
or timeline. More descriptive date ranges, intended for display directly
to the user, *should* be included in the `metadata` property for human
consumption. If the resource contains Canvases that have the `duration`
property, the datetime given corresponds to the navigation datetime of
the start of the resource. For example, a Range that includes a Canvas
that represents a set of video content recording a historical event, the
`navDate` is the datetime of the first moment of the recorded event.

The value *must* be an [XSD dateTime
literal](https://www.w3.org/TR/xmlschema11-2/#dateTime "XSD DateTime").
The value *must* have a timezone, and *should* be given in UTC with the
`Z` timezone indicator, but *may* instead be given as an offset of the
form `+hh:mm`.

- A Collection *may* have the `navDate` property.\
  Clients *may* render `navDate` on a Collection.
- A Manifest *may* have the `navDate` property.\
  Clients *may* render `navDate` on a Manifest.
- A Range *may* have the `navDate` property.\
  Clients *may* render `navDate` on a Range.
- A Canvas *may* have the `navDate` property.\
  Clients *may* render `navDate` on a Canvas.
- Other types of resource *must not* have the `navDate` property.\
  Clients *should* ignore `navDate` on other types of resource.

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{ "navDate": "2010-01-01T00:00:00Z" }
```

</div>

</div>

##### placeholderCanvas <a href="#placeholdercanvas" class="anchorClass"></a>

A single Canvas that provides additional content for use before the main
content of the resource that has the `placeholderCanvas` property is
rendered, or as an advertisement or stand-in for that content. Examples
include images, text and sound standing in for video content before the
user initiates playback; or a film poster to attract user attention. The
content provided by `placeholderCanvas` differs from a thumbnail: a
client might use `thumbnail` to summarize and navigate multiple
resources, then show content from `placeholderCanvas` as part of the
initial presentation of a single resource. A placeholder Canvas is
likely to have different dimensions to those of the Canvas(es) of the
resource that has the `placeholderCanvas` property.

Clients *may* display the content of a linked placeholder Canvas when
presenting the resource. When more than one such Canvas is available,
for example if `placeholderCanvas` is provided for the currently
selected Range and the current Manifest, the client *should* pick the
one most specific to the content. Publishers *should not* assume that
the placeholder Canvas will be processed by all clients. Clients
*should* take care to avoid conflicts between time-based media in the
rendered placeholder Canvas and the content of the resource that has the
`placeholderCanvas` property.

The value *must* be a <span class="abbr"
title="JavaScript Object Notation">JSON</span> object with the `id` and
`type` properties, and *may* have other properties of Canvases. The
value of `type` *must* be the string `Canvas`. The object *must not*
have the `placeholderCanvas` property, nor the `accompanyingCanvas`
property.

- A Collection *may* have the `placeholderCanvas` property.\
  Clients *may* render `placeholderCanvas` on a Collection.
- A Manifest *may* have the `placeholderCanvas` property.\
  Clients *may* render `placeholderCanvas` on a Manifest.
- A Canvas *may* have the `placeholderCanvas` property.\
  Clients *may* render `placeholderCanvas` on a Canvas.
- A Range *may* have the `placeholderCanvas` property.\
  Clients *may* render `placeholderCanvas` on a Range.
- Other types of resource *must not* have the `placeholderCanvas`
  property.\
  Clients *should* ignore `placeholderCanvas` on other types of
  resource.

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "placeholderCanvas": {
    "id": "https://example.org/iiif/1/canvas/placeholder",
    "type": "Canvas",
    "height": 1400,
    "width": 1200
  }
}
```

</div>

</div>

##### accompanyingCanvas <a href="#accompanyingcanvas" class="anchorClass"></a>

A single Canvas that provides additional content for use while rendering
the resource that has the `accompanyingCanvas` property. Examples
include an image to show while a duration-only Canvas is playing audio;
or background audio to play while a user is navigating an image-only
Manifest.

Clients *may* display the content of an accompanying Canvas when
presenting the resource. As with `placeholderCanvas` above, when more
than one accompanying Canvas is available, the client *should* pick the
one most specific to the content. Publishers *should not* assume that
the accompanying Canvas will be processed by all clients. Clients
*should* take care to avoid conflicts between time-based media in the
accompanying Canvas and the content of the resource that has the
`accompanyingCanvas` property.

The value *must* be a <span class="abbr"
title="JavaScript Object Notation">JSON</span> object with the `id` and
`type` properties, and *may* have other properties of Canvases. The
value of `type` *must* be the string `Canvas`. The object *must not*
have the `placeholderCanvas` property, nor the `accompanyingCanvas`
property.

- A Collection *may* have the `accompanyingCanvas` property.\
  Clients *may* render `accompanyingCanvas` on a Collection.
- A Manifest *may* have the `accompanyingCanvas` property.\
  Clients *may* render `accompanyingCanvas` on a Manifest.
- A Canvas *may* have the `accompanyingCanvas` property.\
  Clients *may* render `accompanyingCanvas` on a Canvas.
- A Range *may* have the `accompanyingCanvas` property.\
  Clients *may* render `accompanyingCanvas` on a Range.
- Other types of resource *must not* have the `accompanyingCanvas`
  property.\
  Clients *should* ignore `accompanyingCanvas` on other types of
  resource.

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "accompanyingCanvas": {
    "id": "https://example.org/iiif/1/canvas/accompany",
    "type": "Canvas",
    "duration": 180.0
  }
}
```

</div>

</div>

### 3.2. Technical Properties <a href="#32-technical-properties" class="anchorClass"></a>

These properties describe technical features of the resources, and are
typically processed by the client to understand how to render the
resource.

##### id <a href="#id" class="anchorClass"></a>

The URI that identifies the resource. If the resource is only available
embedded within another resource (see the [terminology
section](/api/presentation/3.0/#12-terminology) for an explanation of
“embedded”), such as a Range within a Manifest, then the URI *may* be
the URI of the embedding resource with a unique fragment on the end.
This is not true for Canvases, which *must* have their own URI without a
fragment.

The value *must* be a string, and the value *must* be an
<span class="abbr" title="Hypertext Transfer Protocol">HTTP</span>(S)
URI for resources defined in this specification. If the resource is
retrievable via <span class="abbr"
title="Hypertext Transfer Protocol">HTTP</span>(S), then the URI *must*
be the URI at which it is published. External resources, such as
profiles, *may* have non-<span class="abbr"
title="Hypertext Transfer Protocol">HTTP</span>(S) URIs defined by other
communities.

The existence of an <span class="abbr"
title="Hypertext Transfer Protocol">HTTP</span>(S) URI in the `id`
property does not mean that the URI will always be dereferencable. If
the resource with the `id` property is
[embedded](/api/presentation/3.0/#12-terminology), it *may* also be
dereferenceable. If the resource is referenced (again, see the
[terminology section](/api/presentation/3.0/#12-terminology) for an
explanation of “referenced”), it *must* be dereferenceable. The
[definitions of the
Resources](/api/presentation/3.0/#5-resource-structure) give further
guidance.

- All resource types *must* have the `id` property.\
  Clients *may* render `id` on any resource type, and *should* render
  `id` on Collections, Manifests and Canvases.

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{ "id": "https://example.org/iiif/1/manifest" }
```

</div>

</div>

##### type <a href="#type" class="anchorClass"></a>

The type or class of the resource. For classes defined for this
specification, the value of `type` will be described in the sections
below describing each individual class.

For content resources, the value of `type` is drawn from other
specifications. Recommendations for common content types such as image,
text or audio are given in the table below.

The <span class="abbr" title="JavaScript Object Notation">JSON</span>
objects that appear in the value of the `service` property will have
many different classes, and can be used to distinguish the sort of
service, with specific properties defined in a [registered context
document](/api/presentation/3.0/#46-linked-data-context-and-extensions "Linked Data Context and Extensions").

The value *must* be a string.

- All resource types *must* have the `type` property.\
  Clients *must* process, and *may* render, `type` on any resource type.

| Class | Description |
|----|----|
| `Dataset` | Data not intended to be rendered to humans directly |
| `Image` | Two dimensional visual resources primarily intended to be seen, such as might be rendered with an \<img\> <span class="abbr" title="HyperText Markup Language">HTML</span> tag |
| `Model` | A three (or more) dimensional model intended to be interacted with by humans |
| `Sound` | Auditory resources primarily intended to be heard, such as might be rendered with an \<audio\> <span class="abbr" title="HyperText Markup Language">HTML</span> tag |
| `Text` | Resources primarily intended to be read |
| `Video` | Moving images, with or without accompanying audio, such as might be rendered with a \<video\> <span class="abbr" title="HyperText Markup Language">HTML</span> tag |

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{ "type": "Image" }
```

</div>

</div>

##### format <a href="#format" class="anchorClass"></a>

The specific media type (often called a MIME type) for a content
resource, for example `image/jpeg`. This is important for distinguishing
different formats of the same overall type of resource, such as
distinguishing text in <span class="abbr"
title="eXtensible Markup Language">XML</span> from plain text.

Note that this is different to the `formats` property in the [Image
<span class="abbr"
title="Application Programming Interface">API</span>](/api/image/3.0/ "Image API"),
which gives the extension to use within that <span class="abbr"
title="Application Programming Interface">API</span>. It would be
inappropriate to use in this case, as `format` can be used with any
content resource, not just images.

The value *must* be a string, and it *should* be the value of the
`Content-Type` header returned when the resource is dereferenced.

- A content resource *should* have the `format` property.\
  Clients *may* render the `format` of any content resource.
- Other types of resource *must not* have the `format` property.\
  Clients *should* ignore `format` on other types of resource.

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{ "format": "application/xml" }
```

</div>

</div>

##### language <a href="#language" class="anchorClass"></a>

The language or languages used in the content of this external resource.
This property is already available from the Web Annotation model for
content resources that are the body or target of an Annotation, however
it *may* also be used for resources
[referenced](/api/presentation/3.0/#12-terminology) from `homepage`,
`rendering`, and `partOf`.

The value *must* be an array of strings. Each item in the array *must*
be a valid language code, as described in the [languages
section](/api/presentation/3.0/#language-of-property-values "Language of Property Values").

- An external resource *should* have the `language` property with at
  least one item.\
  Clients *should* process the `language` of external resources.
- Other types of resource *must not* have the `language` property.\
  Clients *should* ignore `language` on other types of resource.

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{ "language": [ "en" ] }
```

</div>

</div>

##### profile <a href="#profile" class="anchorClass"></a>

A schema or named set of functionality available from the resource. The
profile can further clarify the `type` and/or `format` of an external
resource or service, allowing clients to customize their handling of the
resource that has the `profile` property.

The value *must* be a string, either taken from the [profiles
registry](/api/registry/profiles/) or a URI.

- Resources [referenced](/api/presentation/3.0/#12-terminology) by the
  `seeAlso` or `service` properties *should* have the `profile`
  property.\
  Clients *should* process the `profile` of a service or external
  resource.
- Other types of resource *may* have the `profile` property.\
  Clients *may* process the `profile` of other types of resource.

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{ "profile": "https://example.org/profile/statuary" }
```

</div>

</div>

##### height <a href="#height" class="anchorClass"></a>

The height of the Canvas or external content resource. For content
resources, the value is in pixels. For Canvases, the value does not have
a unit. In combination with the width, it conveys an aspect ratio for
the space in which content resources are located.

The value *must* be a positive integer.

- A Canvas *may* have the `height` property. If it has a `height`, it
  *must* also have a `width`.\
  Clients *must* process `height` on a Canvas.
- Content resources *should* have the `height` property, with the value
  given in pixels, if appropriate to the resource type.\
  Clients *should* process `height` on content resources.
- Other types of resource *must not* have the `height` property.\
  Clients *should* ignore `height` on other types of resource.

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{ "height": 1800 }
```

</div>

</div>

##### width <a href="#width" class="anchorClass"></a>

The width of the Canvas or external content resource. For content
resources, the value is in pixels. For Canvases, the value does not have
a unit. In combination with the height, it conveys an aspect ratio for
the space in which content resources are located.

The value *must* be a positive integer.

- A Canvas *may* have the `width` property. If it has a `width`, it
  *must* also have a `height`.\
  Clients *must* process `width` on a Canvas.
- Content resources *should* have the `width` property, with the value
  given in pixels, if appropriate to the resource type.\
  Clients *should* process `width` on content resources.
- Other types of resource *must not* have the `width` property.\
  Clients *should* ignore `width` on other types of resource.

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{ "width": 1200 }
```

</div>

</div>

##### duration <a href="#duration" class="anchorClass"></a>

The duration of the Canvas or external content resource, given in
seconds.

The value *must* be a positive floating point number.

- A Canvas *may* have the `duration` property.\
  Clients *must* process `duration` on a Canvas.
- Content resources *should* have the `duration` property, if
  appropriate to the resource type.\
  Clients *should* process `duration` on content resources.
- Other types of resource *must not* have a `duration`.\
  Clients *should* ignore `duration` on other types of resource.

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{ "duration": 125.0 }
```

</div>

</div>

##### viewingDirection <a href="#viewingdirection" class="anchorClass"></a>

The direction in which a set of Canvases *should* be displayed to the
user. This specification defines four direction values in the table
below. Others may be defined externally [as an
extension](/api/presentation/3.0/#46-linked-data-context-and-extensions "Linked Data Context and Extensions").

The value *must* be a string.

- A Collection *may* have the `viewingDirection` property.\
  Clients *should* process `viewingDirection` on a Collection.
- A Manifest *may* have the `viewingDirection` property.\
  Clients *should* process `viewingDirection` on a Manifest.
- A Range *may* have the `viewingDirection` property.\
  Clients *may* process `viewingDirection` on a Range.
- Other types of resource *must not* have the `viewingDirection`
  property.\
  Clients *should* ignore `viewingDirection` on other types of resource.

| Value | Description |
|----|----|
| `left-to-right` | The object is displayed from left to right. The default if not specified. |
| `right-to-left` | The object is displayed from right to left. |
| `top-to-bottom` | The object is displayed from the top to the bottom. |
| `bottom-to-top` | The object is displayed from the bottom to the top. |

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{ "viewingDirection": "left-to-right" }
```

</div>

</div>

##### behavior <a href="#behavior" class="anchorClass"></a>

A set of user experience features that the publisher of the content
would prefer the client to use when presenting the resource. This
specification defines the values in the table below. Others may be
defined externally as an
[extension](/api/presentation/3.0/#46-linked-data-context-and-extensions "Linked Data Context and Extensions").

In order to determine the behaviors that are governing a particular
resource, there are four inheritance rules from resources that reference
the current resource:

- Collections inherit behaviors from their referencing Collection.
- Manifests **DO NOT** inherit behaviors from any referencing
  Collections.
- Canvases inherit behaviors from their referencing Manifest, but **DO
  NOT** inherit behaviors from any referencing Ranges, as there might be
  several with different behaviors.
- Ranges inherit behaviors from any referencing Range and referencing
  Manifest.

Clients should interpret behaviors on a Range only when that Range is
selected or is in some other way the context for the user’s current
interaction with the resources. A Range with the `behavior` value
`continuous`, in a Manifest with the `behavior` value `paged`, would
mean that the Manifest’s Canvases should be rendered in a paged fashion,
unless the range is selected to be viewed, and its included Canvases
would be rendered in that context only as being virtually stitched
together. This might occur, for example, when a physical scroll is cut
into pages and bound into a codex with other pages, and the publisher
would like to provide the user the experience of the scroll in its
original form.

The descriptions of the behavior values have a set of which other values
they are disjoint with, meaning that the same resource *must not* have
both of two or more from that set. In order to determine which is in
effect, the client *should* follow the inheritance rules above, taking
the value from the closest resource. The user interface effects of the
possible permutations of non-disjoint behavior values are client
dependent, and implementers are advised to look for relevant recipes in
the [<span class="abbr"
title="International Image Interoperability Framework">IIIF</span>
cookbook](https://iiif.io/api/cookbook/ "IIIF Cookbook").

**Future Clarification Anticipated**\
Further clarifications about the implications of interactions between
behavior values should be expected in subsequent minor releases.

The value *must* be an array of strings.

- Any resource type *may* have the `behavior` property with at least one
  item.\
  Clients *should* process `behavior` on any resource type.

| Value | Description |
|----|----|
|   | **Temporal Behaviors** |
| `auto-advance` | Valid on Collections, Manifests, Canvases, and Ranges that include or are Canvases with at least the `duration` dimension. When the client reaches the end of a Canvas, or segment thereof as specified in a Range, with a duration dimension that has this behavior, it *should* immediately proceed to the next Canvas or segment and render it. If there is no subsequent Canvas in the current context, then this behavior should be ignored. When applied to a Collection, the client should treat the first Canvas of the next Manifest as following the last Canvas of the previous Manifest, respecting any `start` property specified. Disjoint with `no-auto-advance`. |
| `no-auto-advance` | Valid on Collections, Manifests, Canvases, and Ranges that include or are Canvases with at least the `duration` dimension. When the client reaches the end of a Canvas or segment with a duration dimension that has this behavior, it *must not* proceed to the next Canvas, if any. This is a default temporal behavior if not specified. Disjoint with `auto-advance`. |
| `repeat` | Valid on Collections and Manifests, that include Canvases that have at least the `duration` dimension. When the client reaches the end of the duration of the final Canvas in the resource, and the `behavior` value `auto-advance` is also in effect, then the client *should* return to the first Canvas, or segment of Canvas, in the resource that has the `behavior` value `repeat` and start playing again. If the `behavior` value `auto-advance` is not in effect, then the client *should* render a navigation control for the user to manually return to the first Canvas or segment. Disjoint with `no-repeat`. |
| `no-repeat` | Valid on Collections and Manifests, that include Canvases that have at least the `duration` dimension. When the client reaches the end of the duration of the final Canvas in the resource, the client *must not* return to the first Canvas, or segment of Canvas. This is a default temporal behavior if not specified. Disjoint with `repeat`. |
|   | **Layout Behaviors** |
| `unordered` | Valid on Collections, Manifests and Ranges. The Canvases included in resources that have this behavior have no inherent order, and user interfaces *should* avoid implying an order to the user. Disjoint with `individuals`, `continuous`, and `paged`. |
| `individuals` | Valid on Collections, Manifests, and Ranges. For Collections that have this behavior, each of the included Manifests are distinct objects in the given order. For Manifests and Ranges, the included Canvases are distinct views, and *should not* be presented in a page-turning interface. This is the default layout behavior if not specified. Disjoint with `unordered`, `continuous`, and `paged`. |
| `continuous` | Valid on Collections, Manifests and Ranges, which include Canvases that have at least `height` and `width` dimensions. Canvases included in resources that have this behavior are partial views and an appropriate rendering might display all of the Canvases virtually stitched together, such as a long scroll split into sections. This behavior has no implication for audio resources. The `viewingDirection` of the Manifest will determine the appropriate arrangement of the Canvases. Disjoint with `unordered`, `individuals` and `paged`. |
| `paged` | Valid on Collections, Manifests and Ranges, which include Canvases that have at least `height` and `width` dimensions. Canvases included in resources that have this behavior represent views that *should* be presented in a page-turning interface if one is available. The first canvas is a single view (the first recto) and thus the second canvas likely represents the back of the object in the first canvas. If this is not the case, see the `behavior` value `non-paged`. Disjoint with `unordered`, `individuals`, `continuous`, `facing-pages` and `non-paged`. |
| `facing-pages` | Valid only on Canvases, where the Canvas has at least `height` and `width` dimensions. Canvases that have this behavior, in a Manifest that has the `behavior` value `paged`, *must* be displayed by themselves, as they depict both parts of the opening. If all of the Canvases are like this, then page turning is not possible, so simply use `individuals` instead. Disjoint with `paged` and `non-paged`. |
| `non-paged` | Valid only on Canvases, where the Canvas has at least `height` and `width` dimensions. Canvases that have this behavior *must not* be presented in a page turning interface, and *must* be skipped over when determining the page order. This behavior *must* be ignored if the current Manifest does not have the `behavior` value `paged`. Disjoint with `paged` and `facing-pages`. |
|   | **Collection Behaviors** |
| `multi-part` | Valid only on Collections. Collections that have this behavior consist of multiple Manifests or Collections which together form part of a logical whole or a contiguous set, such as multi-volume books or a set of journal issues. Clients might render these Collections as a table of contents rather than with thumbnails, or provide viewing interfaces that can easily advance from one member to the next. Disjoint with `together`. |
| `together` | Valid only on Collections. A client *should* present all of the child Manifests to the user at once in a separate viewing area with its own controls. Clients *should* catch attempts to create too many viewing areas. This behavior *should not* be interpreted as applying to the members of any child resources. Disjoint with `multi-part`. |
|   | **Range Behaviors** |
| `sequence` | Valid only on Ranges, where the Range is [referenced](/api/presentation/3.0/#12-terminology) in the `structures` property of a Manifest. Ranges that have this behavior represent different orderings of the Canvases listed in the `items` property of the Manifest, and user interfaces that interact with this order *should* use the order within the selected Range, rather than the default order of `items`. Disjoint with `thumbnail-nav` and `no-nav`. |
| `thumbnail-nav` | Valid only on Ranges. Ranges that have this behavior *may* be used by the client to present an alternative navigation or overview based on thumbnails, such as regular keyframes along a timeline for a video, or sections of a long scroll. Clients *should not* use them to generate a conventional table of contents. Child Ranges of a Range with this behavior *must* have a suitable `thumbnail` property. Disjoint with `sequence` and `no-nav`. |
| `no-nav` | Valid only on Ranges. Ranges that have this behavior *must not* be displayed to the user in a navigation hierarchy. This allows for Ranges to be present that capture unnamed regions with no interesting content, such as the set of blank pages at the beginning of a book, or dead air between parts of a performance, that are still part of the Manifest but do not need to be navigated to directly. Disjoint with `sequence` and `thumbnail-nav`. |
|   | **Miscellaneous Behaviors** |
| `hidden` | Valid on Annotation Collections, Annotation Pages, Annotations, Specific Resources and Choices. If this behavior is provided, then the client *should not* render the resource by default, but allow the user to turn it on and off. This behavior does not inherit, as it is not valid on Collections, Manifests, Ranges or Canvases. |

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{ "behavior": [ "auto-advance", "individuals" ] }
```

</div>

</div>

##### timeMode <a href="#timemode" class="anchorClass"></a>

A mode associated with an Annotation that is to be applied to the
rendering of any time-based media, or otherwise could be considered to
have a duration, used as a body resource of that Annotation. Note that
the association of `timeMode` with the Annotation means that different
resources in the body cannot have different values. This specification
defines the values specified in the table below. Others may be defined
externally as an
[extension](/api/presentation/3.0/#46-linked-data-context-and-extensions "Linked Data Context and Extensions").

The value *must* be a string.

- An Annotation *may* have the `timeMode` property.\
  Clients *should* process `timeMode` on an Annotation.

| Value | Description |
|----|----|
| `trim` | (default, if not supplied) If the content resource has a longer duration than the duration of portion of the Canvas it is associated with, then at the end of the Canvas’s duration, the playback of the content resource *must* also end. If the content resource has a shorter duration than the duration of the portion of the Canvas it is associated with, then, for video resources, the last frame *should* persist on-screen until the end of the Canvas portion’s duration. For example, a video of 120 seconds annotated to a Canvas with a duration of 100 seconds would play only the first 100 seconds and drop the last 20 second. |
| `scale` | Fit the duration of content resource to the duration of the portion of the Canvas it is associated with by scaling. For example, a video of 120 seconds annotated to a Canvas with a duration of 60 seconds would be played at double-speed. |
| `loop` | If the content resource is shorter than the `duration` of the Canvas, it *must* be repeated to fill the entire duration. Resources longer than the `duration` *must* be trimmed as described above. For example, if a 20 second duration audio stream is annotated onto a Canvas with duration 30 seconds, it will be played one and a half times. |

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{ "timeMode": "trim" }
```

</div>

</div>

### 3.3. Linking Properties <a href="#33-linking-properties" class="anchorClass"></a>

These properties are references or links between resources, and split
into external references where the linked object is outside of the
<span class="abbr"
title="International Image Interoperability Framework">IIIF</span>
space, and internal references where the linked object is a
<span class="abbr"
title="International Image Interoperability Framework">IIIF</span>
resource. Clients typically create a link to the resource that is able
to be activated by the user, or interact directly with the linked
resource to improve the user’s experience.

#### 3.3.1. External Links <a href="#331-external-links" class="anchorClass"></a>

##### homepage <a href="#homepage" class="anchorClass"></a>

A web page that is about the object represented by the resource that has
the `homepage` property. The web page is usually published by the
organization responsible for the object, and might be generated by a
content management system or other cataloging system. The resource
*must* be able to be displayed directly to the user. Resources that are
related, but not home pages, *must* instead be added into the `metadata`
property, with an appropriate `label` or `value` to describe the
relationship.

The value of this property *must* be an array of <span class="abbr"
title="JavaScript Object Notation">JSON</span> objects, each of which
*must* have the `id`, `type`, and `label` properties, *should* have a
`format` property, and *may* have the `language` property.

- Any resource type *may* have the `homepage` property.\
  Clients *should* render `homepage` on a Collection, Manifest or
  Canvas, and *may* render `homepage` on other types of resource.

**Model Alignment**\
Please note that this specification has stricter requirements about the
<span class="abbr" title="JavaScript Object Notation">JSON</span>
pattern used for the `homepage` property than the [Web Annotation Data
Model](http://w3.org/TR/annotation-model/ "Web Annotation Model"). The
<span class="abbr"
title="International Image Interoperability Framework">IIIF</span>
requirements are compatible, but the home page of an Agent found might
have only a URI, or might be a <span class="abbr"
title="JavaScript Object Notation">JSON</span> object with other
properties. See the section on [collisions between
contexts](/api/presentation/3.0/#47-term-collisions-between-contexts)
for more information.

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "homepage": [
    {
      "id": "https://example.com/info/",
      "type": "Text",
      "label": { "en": [ "Homepage for Example Object" ] },
      "format": "text/html",
      "language": [ "en" ]
    }
  ]
}
```

</div>

</div>

##### logo <a href="#logo" class="anchorClass"></a>

A small image resource that represents the Agent resource it is
associated with. The logo *must* be clearly rendered when the resource
is displayed or used, without cropping, rotating or otherwise distorting
the image. It is *recommended* that a [<span class="abbr"
title="International Image Interoperability Framework">IIIF</span> Image
<span class="abbr"
title="Application Programming Interface">API</span>](/api/image/3.0/ "Image API")
service be available for this image for other manipulations such as
resizing.

When more than one logo is present, the client *should* pick only one of
them, based on the information in the logo properties. For example, the
client could select a logo of appropriate aspect ratio based on the
`height` and `width` properties of the available logos. The client *may*
decide on the logo by inspecting properties defined as
[extensions](/api/presentation/3.0/#46-linked-data-context-and-extensions "Linked Data Context and Extensions").

The value of this property *must* be an array of <span class="abbr"
title="JavaScript Object Notation">JSON</span> objects, each of which
*must* have `id` and `type` properties, and *should* have `format`. The
value of `type` *must* be “Image”.

- Agent resources *should* have the `logo` property.\
  Clients *must* render `logo` on Agent resources.

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "logo": [
    {
      "id": "https://example.org/img/logo.jpg",
      "type": "Image",
      "format": "image/jpeg",
      "height": 100,
      "width": 120
    }
  ]
}
```

</div>

</div>

##### rendering <a href="#rendering" class="anchorClass"></a>

A resource that is an alternative, non-<span class="abbr"
title="International Image Interoperability Framework">IIIF</span>
representation of the resource that has the `rendering` property. Such
representations typically cannot be painted onto a single Canvas, as
they either include too many views, have incompatible dimensions, or are
compound resources requiring additional rendering functionality. The
`rendering` resource *must* be able to be displayed directly to a human
user, although the presentation may be outside of the <span class="abbr"
title="International Image Interoperability Framework">IIIF</span>
client. The resource *must not* have a splash page or other interstitial
resource that mediates access to it. If access control is required, then
the [<span class="abbr"
title="International Image Interoperability Framework">IIIF</span>
Authentication <span class="abbr"
title="Application Programming Interface">API</span>](/api/auth/ "IIIF Authentication API")
is *recommended*. Examples include a rendering of a book as a PDF or
EPUB, a slide deck with images of a building, or a 3D model of a statue.

The value *must* be an array of <span class="abbr"
title="JavaScript Object Notation">JSON</span> objects. Each item *must*
have the `id`, `type` and `label` properties, and *should* have a
`format` property.

- Any resource type *may* have the `rendering` property with at least
  one item.\
  Clients *should* render `rendering` on a Collection, Manifest or
  Canvas, and *may* render `rendering` on other types of resource.

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "rendering": [
    {
      "id": "https://example.org/1.pdf",
      "type": "Text",
      "label": { "en": [ "PDF Rendering of Book" ] },
      "format": "application/pdf"
    }
  ]
}
```

</div>

</div>

##### service <a href="#service" class="anchorClass"></a>

A service that the client might interact with directly and gain
additional information or functionality for using the resource that has
the `service` property, such as from an Image to the base URI of an
associated [<span class="abbr"
title="International Image Interoperability Framework">IIIF</span> Image
<span class="abbr"
title="Application Programming Interface">API</span>](/api/image/3.0/ "Image API")
service. The service resource *should* have additional information
associated with it in order to allow the client to determine how to make
appropriate use of it. Please see the [Service
Registry](/api/registry/services/) document for the details of currently
known service types.

The value *must* be an array of <span class="abbr"
title="JavaScript Object Notation">JSON</span> objects. Each object will
have properties depending on the service’s definition, but *must* have
either the `id` or `@id` and `type` or `@type` properties. Each object
*should* have a `profile` property.

- Any resource type *may* have the `service` property with at least one
  item.\
  Clients *may* process `service` on any resource type, and *should*
  process the <span class="abbr"
  title="International Image Interoperability Framework">IIIF</span>
  Image <span class="abbr"
  title="Application Programming Interface">API</span> service.

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "service": [
    {
      "id": "https://example.org/service",
      "type": "ExampleExtensionService",
      "profile": "https://example.org/docs/service"
    }
  ]
}
```

</div>

</div>

For cross-version consistency, this specification defines the following
values for the `type` or `@type` property for backwards compatibility
with other <span class="abbr"
title="International Image Interoperability Framework">IIIF</span> APIs.
Future versions of these APIs will define their own types. These `type`
values are necessary extensions for compatibility of the older versions.

| Value | Specification |
|----|----|
| ImageService1 | [Image <span class="abbr" title="Application Programming Interface">API</span> version 1](/api/image/1.1/ "Image API 1.1") |
| ImageService2 | [Image <span class="abbr" title="Application Programming Interface">API</span> version 2](/api/image/2.1/ "Image API 2.1") |
| SearchService1 | [Search <span class="abbr" title="Application Programming Interface">API</span> version 1](/api/search/1.0/) |
| AutoCompleteService1 | [Search <span class="abbr" title="Application Programming Interface">API</span> version 1](/api/search/1.0/#autocomplete) |
| AuthCookieService1 | [Authentication <span class="abbr" title="Application Programming Interface">API</span> version 1](/api/auth/1.0/#access-cookie-service "IIIF Authentication Cookie Service") |
| AuthTokenService1 | [Authentication <span class="abbr" title="Application Programming Interface">API</span> version 1](/api/auth/1.0/#access-token-service "IIIF Authentication Access Token Service") |
| AuthLogoutService1 | [Authentication <span class="abbr" title="Application Programming Interface">API</span> version 1](/api/auth/1.0/#logout-service "IIIF Authentication Logout Service") |

Implementations *should* be prepared to recognize the `@id` and `@type`
property names used by older specifications, as well as `id` and `type`.
Note that the `@context` key *should not* be present within the
`service`, but instead included at the beginning of the document. The
example below includes both version 2 and version 3 <span class="abbr"
title="International Image Interoperability Framework">IIIF</span> Image
<span class="abbr" title="Application Programming Interface">API</span>
services.

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "service": [
    {
      "@id": "https://example.org/iiif2/image1/identifier",
      "@type": "ImageService2",
      "profile": "http://iiif.io/api/image/2/level2.json"
    },
    {
      "id": "https://example.org/iiif3/image1/identifier",
      "type": "ImageService3",
      "profile": "level2"
    }
  ]
}
```

</div>

</div>

##### services <a href="#services" class="anchorClass"></a>

A list of one or more service definitions on the top-most resource of
the document, that are typically shared by more than one subsequent
resource. This allows for these shared services to be collected together
in a single place, rather than either having their information
duplicated potentially many times throughout the document, or requiring
a consuming client to traverse the entire document structure to find the
information. The resource that the service applies to *must* still have
the `service` property, as described above, where the service resources
have at least the `id` and `type` or `@id` and `@type` properties. This
allows the client to know that the service applies to that resource.
Usage of the `services` property is at the discretion of the publishing
system.

A client encountering a `service` property where the definition consists
only of an `id` and `type` *should* then check the `services` property
on the top-most resource for an expanded definition. If the service is
not present in the `services` list, and the client requires more
information in order to use the service, then it *should* dereference
the `id` (or `@id`) of the service in order to retrieve a service
description.

The value *must* be an array of <span class="abbr"
title="JavaScript Object Notation">JSON</span> objects. Each object
*must* a service resource, as described above.

- A Collection *may* have the `services` property, if it is the topmost
  Collection in a response document.\
  Clients *should* process `services` on a Collection.
- A Manifest *may* have the `services` property.\
  Clients *should* process `services` on a Manifest.

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "services": [
    {
      "@id": "https://example.org/iiif/auth/login",
      "@type": "AuthCookieService1",
      "profile": "http://iiif.io/api/auth/1/login",
      "label": "Login to Example Institution",
      "service": [
        {
          "@id": "https://example.org/iiif/auth/token",
          "@type": "AuthTokenService1",
          "profile": "http://iiif.io/api/auth/1/token"          
        }
      ]
    }
  ]
}
```

</div>

</div>

##### seeAlso <a href="#seealso" class="anchorClass"></a>

A machine-readable resource such as an <span class="abbr"
title="eXtensible Markup Language">XML</span> or <span class="abbr"
title="Resource Description Framework">RDF</span> description that is
related to the current resource that has the `seeAlso` property.
Properties of the resource should be given to help the client select
between multiple descriptions (if provided), and to make appropriate use
of the document. If the relationship between the resource and the
document needs to be more specific, then the document should include
that relationship rather than the <span class="abbr"
title="International Image Interoperability Framework">IIIF</span>
resource. Other <span class="abbr"
title="International Image Interoperability Framework">IIIF</span>
resources are also valid targets for `seeAlso`, for example to link to a
Manifest that describes a related object. The URI of the document *must*
identify a single representation of the data in a particular format. For
example, if the same data exists in <span class="abbr"
title="JavaScript Object Notation">JSON</span> and <span class="abbr"
title="eXtensible Markup Language">XML</span>, then separate resources
should be added for each representation, with distinct `id` and `format`
properties.

The value *must* be an array of <span class="abbr"
title="JavaScript Object Notation">JSON</span> objects. Each item *must*
have the `id` and `type` properties, and *should* have the `label`,
`format` and `profile` properties.

- Any resource type *may* have the `seeAlso` property with at least one
  item.\
  Clients *may* process `seeAlso` on any resource type.

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "seeAlso": [
    {
      "id": "https://example.org/library/catalog/book1.xml",
      "type": "Dataset",
      "label": { "en": [ "Bibliographic Description in XML" ] },
      "format": "text/xml",
      "profile": "https://example.org/profiles/bibliographic"
    }
  ]
}
```

</div>

</div>

#### 3.3.2. Internal Links <a href="#332-internal-links" class="anchorClass"></a>

##### partOf <a href="#partof" class="anchorClass"></a>

A containing resource that includes the resource that has the `partOf`
property. When a client encounters the `partOf` property, it might
retrieve the [referenced](/api/presentation/3.0/#12-terminology)
containing resource, if it is not
[embedded](/api/presentation/3.0/#12-terminology) in the current
representation, in order to contribute to the processing of the
contained resource. For example, the `partOf` property on a Canvas can
be used to reference an external Manifest in order to enable the
discovery of further relevant information. Similarly, a Manifest can
reference a containing Collection using `partOf` to aid in navigation.

The value *must* be an array of <span class="abbr"
title="JavaScript Object Notation">JSON</span> objects. Each item *must*
have the `id` and `type` properties, and *should* have the `label`
property.

- Any resource type *may* have the `partOf` property with at least one
  item\
  Clients *may* render `partOf` on any resource type.

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{ "partOf": [ { "id": "https://example.org/iiif/1", "type": "Manifest" } ] }
```

</div>

</div>

##### start <a href="#start" class="anchorClass"></a>

A Canvas, or part of a Canvas, which the client *should* show on
initialization for the resource that has the `start` property. The
reference to part of a Canvas is handled in the same way that Ranges
reference parts of Canvases. This property allows the client to begin
with the first Canvas that contains interesting content rather than
requiring the user to manually navigate to find it.

The value *must* be a <span class="abbr"
title="JavaScript Object Notation">JSON</span> object, which *must* have
the `id` and `type` properties. The object *must* be either a Canvas (as
in the first example below), or a Specific Resource with a Selector and
a `source` property where the value is a Canvas (as in the second
example below).

- A Manifest *may* have the `start` property.\
  Clients *should* process `start` on a Manifest.
- A Range *may* have the `start` property.\
  Clients *should* process `start` on a Range.
- Other types of resource *must not* have the `start` property.\
  Clients *should* ignore `start` on other types of resource.

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{ "start": { "id": "https://example.org/iiif/1/canvas/1", "type": "Canvas" } }
```

</div>

</div>

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "start": {
    "id": "https://example.org/iiif/1/canvas-segment/1",
    "type": "SpecificResource",
    "source": "https://example.org/iiif/1/canvas/1",
    "selector": {
      "type": "PointSelector",
      "t": 14.5
    }
  }
}
```

</div>

</div>

##### supplementary <a href="#supplementary" class="anchorClass"></a>

A link from this Range to an Annotation Collection that includes the
`supplementing` Annotations of content resources for the Range. Clients
might use this to present additional content to the user from a
different Canvas when interacting with the Range, or to jump to the next
part of the Range within the same Canvas. For example, the Range might
represent a newspaper article that spans non-sequential pages, and then
uses the `supplementary` property to reference an Annotation Collection
that consists of the Annotations that record the text, split into
Annotation Pages per newspaper page. Alternatively, the Range might
represent the parts of a manuscript that have been transcribed or
translated, when there are other parts that have yet to be worked on.
The Annotation Collection would be the Annotations that transcribe or
translate, respectively.

The value *must* be a <span class="abbr"
title="JavaScript Object Notation">JSON</span> object, which *must* have
the `id` and `type` properties, and the `type` *must* be
`AnnotationCollection`.

- A Range *may* have the `supplementary` property.\
  Clients *may* process `supplementary` on a Range.
- Other types of resource *must not* have the `supplementary` property.\
  Clients *should* ignore `supplementary` on other types of resource.

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{ "supplementary": { "id": "https://example.org/iiif/1/annos/1", "type": "AnnotationCollection" } }
```

</div>

</div>

### 3.4. Structural Properties <a href="#34-structural-properties" class="anchorClass"></a>

These properties define the structure of the object being represented in
<span class="abbr"
title="International Image Interoperability Framework">IIIF</span> by
allowing the inclusion of child resources within parents, such as a
Canvas within a Manifest, or a Manifest within a Collection. The
majority of cases use `items`, however there are two special cases for
different sorts of structures.

##### items <a href="#items" class="anchorClass"></a>

Much of the functionality of the <span class="abbr"
title="International Image Interoperability Framework">IIIF</span>
Presentation <span class="abbr"
title="Application Programming Interface">API</span> is simply recording
the order in which child resources occur within a parent resource, such
as Collections or Manifests within a parent Collection, or Canvases
within a Manifest. All of these situations are covered with a single
property, `items`.

The value *must* be an array of <span class="abbr"
title="JavaScript Object Notation">JSON</span> objects. Each item *must*
have the `id` and `type` properties. The items will be resources of
different types, as described below.

- A Collection *must* have the `items` property. Each item *must* be
  either a Collection or a Manifest.\
  Clients *must* process `items` on a Collection.
- A Manifest *must* have the `items` property with at least one item.
  Each item *must* be a Canvas.\
  Clients *must* process `items` on a Manifest.
- A Canvas *should* have the `items` property with at least one item.
  Each item *must* be an Annotation Page.\
  Clients *must* process `items` on a Canvas.
- An Annotation Page *should* have the `items` property with at least
  one item. Each item *must* be an Annotation.\
  Clients *must* process `items` on an Annotation Page.
- A Range *must* have the `items` property with at least one item. Each
  item *must* be a Range, a Canvas or a Specific Resource where the
  source is a Canvas.\
  Clients *should* process `items` on a Range.
- Other types of resource *must not* have the `items` property.\
  Clients *should* ignore `items` on other types of resource.

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "items": [
    {
      "id": "https://example.org/iiif/manifest1",
      "type": "Manifest"
    },
    {
      "id": "https://example.org/iiif/collection1",
      "type": "Collection"
    }
    // ...
  ]
}
```

</div>

</div>

##### structures <a href="#structures" class="anchorClass"></a>

The structure of an object represented as a Manifest can be described
using a hierarchy of Ranges. Ranges can be used to describe the “table
of contents” of the object or other structures that the user can
interact with beyond the order given by the `items` property of the
Manifest. The hierarchy is built by nesting the child Range resources in
the `items` array of the higher level Range. The top level Ranges of
these hierarchies are given in the `structures` property.

The value *must* be an array of <span class="abbr"
title="JavaScript Object Notation">JSON</span> objects. Each item *must*
have the `id` and `type` properties, and the `type` *must* be `Range`.

- A Manifest *may* have the `structures` property.\
  Clients *should* process `structures` on a Manifest. The first
  hierarchy *should* be presented to the user by default, and further
  hierarchies *should* be able to be selected as alternative structures
  by the user.
- Other types of resource *must not* have the `structures` property.\
  Clients *should* ignore `structures` on other types of resource.

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "structures": [
    {
      "id": "https://example.org/iiif/range/1",
      "type": "Range",
      "items": [ { ... } ]
    }
  ]
}
```

</div>

</div>

##### annotations <a href="#annotations" class="anchorClass"></a>

An ordered list of Annotation Pages that contain commentary or other
Annotations about this resource, separate from the Annotations that are
used to paint content on to a Canvas. The `motivation` of the
Annotations *must not* be `painting`, and the target of the Annotations
*must* include this resource or part of it.

The value *must* be an array of <span class="abbr"
title="JavaScript Object Notation">JSON</span> objects. Each item *must*
have at least the `id` and `type` properties.

- A Collection *may* have the `annotations` property with at least one
  item.\
  Clients *should* process `annotations` on a Collection.
- A Manifest *may* have the `annotations` property with at least one
  item.\
  Clients *should* process `annotations` on a Manifest,.
- A Canvas *may* have the `annotations` property with at least one
  item.\
  Clients *should* process `annotations` on a Canvas.
- A Range *may* have the `annotations` property with at least one item.\
  Clients *should* process `annotations` on a Range.
- A content resource *may* have the `annotations` property with at least
  one item.\
  Clients *should* process `annotations` on a content resource.
- Other types of resource *must not* have the `annotations` property.\
  Clients *should* ignore `annotations` on other types of resource.

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "annotations": [
    {
      "id": "https://example.org/iiif/annotationPage/1",
      "type": "AnnotationPage",
      "items": [ { ... } ]
    }
  ]
}
```

</div>

</div>

### 3.5. Values <a href="#35-values" class="anchorClass"></a>

##### Values for motivation <a href="#values-for-motivation" class="anchorClass"></a>

This specification defines two values for the Web Annotation property of
`motivation`, or `purpose` when used on a Specific Resource or Textual
Body.

While any resource *may* be the `target` of an Annotation, this
specification defines only motivations for Annotations that target
Canvases. These motivations allow clients to determine how the
Annotation should be rendered, by distinguishing between Annotations
that provide the content of the Canvas, from ones with externally
defined motivations which are typically comments about the Canvas.

Additional motivations may be added to the Annotation to further clarify
the intent, drawn from
[extensions](/api/presentation/3.0/#46-linked-data-context-and-extensions "Linked Data Context and Extensions")
or other sources. Clients *must* ignore motivation values that they do
not understand. Other motivation values given in the Web Annotation
specification *should* be used where appropriate, and examples are given
in the [Presentation <span class="abbr"
title="Application Programming Interface">API</span>
Cookbook](https://iiif.io/api/cookbook/ "IIIF Cookbook").

| Value | Description |
|----|----|
| `painting` | Resources associated with a Canvas by an Annotation that has the `motivation` value `painting` *must* be presented to the user as the representation of the Canvas. The content can be thought of as being *of* the Canvas. The use of this motivation with target resources other than Canvases is undefined. For example, an Annotation that has the `motivation` value `painting`, a body of an Image and the target of the Canvas is an instruction to present that Image as (part of) the visual representation of the Canvas. Similarly, a textual body is to be presented as (part of) the visual representation of the Canvas and not positioned in some other part of the user interface. |
| `supplementing` | Resources associated with a Canvas by an Annotation that has the `motivation` value `supplementing` *may* be presented to the user as part of the representation of the Canvas, or *may* be presented in a different part of the user interface. The content can be thought of as being *from* the Canvas. The use of this motivation with target resources other than Canvases is undefined. For example, an Annotation that has the `motivation` value `supplementing`, a body of an Image and the target of part of the Canvas is an instruction to present that Image to the user either in the Canvas’s rendering area or somewhere associated with it, and could be used to present an easier to read representation of a diagram. Similarly, a textual body is to be presented either in the targeted region of the Canvas or otherwise associated with it, and might be OCR, a manual transcription or a translation of handwritten text, or captions for what is being said in a Canvas with audio content. |

## 4. <span class="abbr" title="JSON for Linking Data">JSON-LD</span> Considerations <a href="#4-json-ld-considerations" class="anchorClass"></a>

This section describes features applicable to all of the Presentation
<span class="abbr" title="Application Programming Interface">API</span>
content. For the most part, these are features of the <span class="abbr"
title="JSON for Linking Data">JSON-LD</span> specification that have
particular uses within the <span class="abbr"
title="Application Programming Interface">API</span>.

### 4.1. Case Sensitivity <a href="#41-case-sensitivity" class="anchorClass"></a>

Terms in <span class="abbr" title="JSON for Linking Data">JSON-LD</span>
are [case
sensitive](https://www.w3.org/TR/json-ld11/#the-context "JSON-LD Context").
The cases of properties and enumerated values in <span class="abbr"
title="International Image Interoperability Framework">IIIF</span>
Presentation <span class="abbr"
title="Application Programming Interface">API</span> responses *must*
match those used in this specification. For example to specify that a
resource is a Manifest, the property *must* be given as `type` and not
`Type` or `tYpE`, and the value *must* be given as `Manifest` and not
`manifest` or `manIfEsT`.

### 4.2. Resource Representations <a href="#42-resource-representations" class="anchorClass"></a>

Resource descriptions *should* be
[embedded](/api/presentation/3.0/#12-terminology) within the
<span class="abbr" title="JavaScript Object Notation">JSON</span>
description of parent resources, and *may* also be available via
separate requests from the <span class="abbr"
title="Hypertext Transfer Protocol">HTTP</span>(S) URI given in the
resource’s `id` property. Links to resources *must* be given as a
<span class="abbr" title="JavaScript Object Notation">JSON</span> object
with the `id` and `type` properties and *should* have `format` or
`profile` to give a hint as to what sort of resource is being referred
to.

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "rendering": [
    {
      "id": "https://example.org/content/book.pdf",
      "type": "Text",
      "label": { "en": [ "Example Book (pdf)" ] },
      "format": "application/pdf"
    }
  ]
}
```

</div>

</div>

### 4.3. Properties with Multiple Values <a href="#43-properties-with-multiple-values" class="anchorClass"></a>

Any of the properties in the <span class="abbr"
title="Application Programming Interface">API</span> that can have
multiple values *must* always be given as an array of values, even if
there is only a single item in that array.

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "thumbnail": [
    {
      "id": "https://example.org/images/thumb1.jpg",
      "type": "Image",
      "format": "image/jpeg"
    }
  ]
}
```

</div>

</div>

### 4.4. Language of Property Values <a href="#language-of-property-values" class="anchorClass"></a>

Language *may* be associated with strings that are intended to be
displayed to the user for the `label` and `summary` properties, plus the
`label` and `value` properties of the `metadata` and `requiredStatement`
objects.

The values of these properties *must* be <span class="abbr"
title="JavaScript Object Notation">JSON</span> objects, with the keys
being the [BCP
47](https://tools.ietf.org/html/bcp47 "Tags for Identifying Languages")
language code for the language, or if the language is either not known
or the string does not have a language, then the key *must* be the
string `none`. The associated values *must* be arrays of strings, where
each item is the content in the given language.

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "label": {
    "en": [
      "Whistler's Mother",
      "Arrangement in Grey and Black No. 1: The Artist's Mother"
    ],
    "fr": [
      "Arrangement en gris et noir no 1",
      "Portrait de la mère de l'artiste",
      "La Mère de Whistler"
    ],
    "none": [ "Whistler (1871)" ]
  }
}
```

</div>

</div>

Note that [BCP
47](https://tools.ietf.org/html/bcp47 "Tags for Identifying Languages")
allows the script of the text to be included after a hyphen, such as
`ar-latn`, and clients should be aware of this possibility.

In the case where multiple values are supplied, clients *must* use the
following algorithm to determine which values to display to the user.

- If all of the values are associated with the `none` key, the client
  *must* display all of those values.
- Else, the client should try to determine the user’s language
  preferences, or failing that use some default language preferences.
  Then:
  - If any of the values have a language associated with them, the
    client *must* display all of the values associated with the language
    that best matches the language preference.
  - If all of the values have a language associated with them, and none
    match the language preference, the client *must* select a language
    and display all of the values associated with that language.
  - If some of the values have a language associated with them, but none
    match the language preference, the client *must* display all of the
    values that do not have a language associated with them.

Note that this does not apply to
[embedded](/api/presentation/3.0/#12-terminology) textual bodies in
Annotations, which use the Web Annotation pattern of `value` and
`language` as separate properties.

### 4.5. <span class="abbr" title="HyperText Markup Language">HTML</span> Markup in Property Values <a href="#45-html-markup-in-property-values" class="anchorClass"></a>

Minimal <span class="abbr" title="HyperText Markup Language">HTML</span>
markup *may* be included for processing in the `summary` property and
the `value` property in the `metadata` and `requiredStatement` objects.
It *must not* be used in `label` or other properties. This is included
to allow content publishers to add links and simple formatting
instructions to blocks of text. The content *must* be well-formed
<span class="abbr" title="eXtensible Markup Language">XML</span> and
therefore *must* be wrapped in an element such as `p` or `span`. There
*must not* be whitespace on either side of the <span class="abbr"
title="HyperText Markup Language">HTML</span> string, and thus the first
character in the string *must* be a ‘\<’ character and the last
character *must* be ‘\>’, allowing a consuming application to test
whether the value is <span class="abbr"
title="HyperText Markup Language">HTML</span> or plain text using these.
To avoid a non-<span class="abbr"
title="HyperText Markup Language">HTML</span> string matching this, it
is *recommended* that an additional whitespace character be added to the
end of the value in situations where plain text happens to start and end
this way.

In order to avoid <span class="abbr"
title="HyperText Markup Language">HTML</span> or script injection
attacks, clients *must* remove:

- Tags such as `script`, `style`, `object`, `form`, `input` and similar.
- All attributes other than `href` on the `a` tag, `src` and `alt` on
  the `img` tag.
- All `href` attributes that start with the strings other than “http:”,
  “https:”, and “mailto:”.
- CData sections.
- <span class="abbr" title="eXtensible Markup Language">XML</span>
  Comments.
- Processing instructions.

Clients *should* allow only `a`, `b`, `br`, `i`, `img`, `p`, `small`,
`span`, `sub` and `sup` tags. Clients *may* choose to remove any and all
tags, therefore it *should not* be assumed that the formatting will
always be rendered. Note that publishers *may* include arbitrary
<span class="abbr" title="HyperText Markup Language">HTML</span> content
for processing using customized or experimental applications, and the
requirements for clients assume an untrusted or unknown publisher.

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{ "summary": { "en-latn": [ "<p>Short <b>summary</b> of the resource.</p>" ] } }
```

</div>

</div>

### 4.6. Linked Data Context and Extensions <a href="#46-linked-data-context-and-extensions"
class="anchorClass"></a>

The top level resource in the response *must* have the `@context`
property, and it *should* appear as the very first key/value pair of the
<span class="abbr" title="JavaScript Object Notation">JSON</span>
representation. This tells Linked Data processors how to interpret the
document. The <span class="abbr"
title="International Image Interoperability Framework">IIIF</span>
Presentation <span class="abbr"
title="Application Programming Interface">API</span> context, below,
*must* occur once per response in the top-most resource, and thus *must
not* appear within [embedded](/api/presentation/3.0/#12-terminology)
resources. For example, when embedding a Canvas within a Manifest, the
Canvas will not have the `@context` property.

The value of the `@context` property *must* be either the URI
`http://iiif.io/api/presentation/3/context.json` or a <span class="abbr"
title="JavaScript Object Notation">JSON</span> array with the URI
`http://iiif.io/api/presentation/3/context.json` as the last item.
Further contexts, such as those for local or [registered
extensions](/api/registry/ "IIIF Extension Registry"), *must* be added
at the beginning of the array.

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "@context": "http://iiif.io/api/presentation/3/context.json"
}
```

</div>

</div>

Any additional properties beyond those defined in this specification or
the Web Annotation Data Model *should* be mapped to <span class="abbr"
title="Resource Description Framework">RDF</span> predicates using
further context documents. These extensions *should* be added to the top
level `@context` property, and *must* be added before the above context.
The <span class="abbr" title="JSON for Linking Data">JSON-LD</span> 1.1
functionality of predicate specific context definitions, known as
[scoped
contexts](https://json-ld.org/spec/latest/json-ld/#scoped-contexts "JSON-LD Scoped Contexts"),
*must* be used to minimize cross-extension collisions. Extensions
intended for community use *should* be [registered in the extensions
registry](/api/registry/ "IIIF Extension Registry"), but registration is
not mandatory.

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "@context": [
    "http://example.org/extension/context.json",
    "http://iiif.io/api/presentation/3/context.json"
  ]
}
```

</div>

</div>

The <span class="abbr" title="JavaScript Object Notation">JSON</span>
representation *must not* include the `@graph` key at the top level.
This key might be created when serializing directly from
<span class="abbr" title="Resource Description Framework">RDF</span>
data using the <span class="abbr"
title="JSON for Linking Data">JSON-LD</span> 1.0 compaction algorithm.
Instead, <span class="abbr" title="JSON for Linking Data">JSON-LD</span>
framing and/or custom code should be used to ensure the structure of the
document is as defined by this specification.

### 4.7. Term Collisions between Contexts <a href="#47-term-collisions-between-contexts" class="anchorClass"></a>

There are some common terms used in more than one <span class="abbr"
title="JSON for Linking Data">JSON-LD</span> context document. Every
attempt has been made to minimize these collisions, but some are
inevitable. In order to know which specification is in effect at any
given point, the class of the resource that has the property is the
primary governing factor. Thus properties on Annotation based resources
use the context from the [Web Annotation Data
Model](http://w3.org/TR/annotation-model/ "Web Annotation Model"),
whereas properties on classes defined by this specification use the
<span class="abbr"
title="International Image Interoperability Framework">IIIF</span>
Presentation <span class="abbr"
title="Application Programming Interface">API</span> context’s
definition.

There is one property that is in direct conflict - the `label` property
is defined by both and is available for every resource. The use of
`label` in <span class="abbr"
title="International Image Interoperability Framework">IIIF</span>
follows modern best practices for internationalization by allowing the
language to be associated with the value using the language map
construction [described
above](/api/presentation/3.0/#language-of-property-values "Language of Property Values").
The Web Annotation Data Model uses it only for [Annotation
Collections](/api/presentation/3.0/#58-annotation-collection), and
mandates the format is a string. For this property, the
<span class="abbr" title="Application Programming Interface">API</span>
overrides the definition from the Annotation model to ensure that labels
can consistently be represented in multiple languages.

The following properties are defined by both, and the <span class="abbr"
title="International Image Interoperability Framework">IIIF</span>
representation is more specific than the Web Annotation Data Model but
are not in conflict, or are never used on the same resource:

- `homepage`: In <span class="abbr"
  title="International Image Interoperability Framework">IIIF</span> the
  home page of a resource is represented as a <span class="abbr"
  title="JavaScript Object Notation">JSON</span> object, whereas in the
  Web Annotation Data Model it can also be a string.
- `type`: In <span class="abbr"
  title="International Image Interoperability Framework">IIIF</span> the
  type is singular, whereas in the Web Annotation Data Model there can
  be more than one type.
- `format`: In <span class="abbr"
  title="International Image Interoperability Framework">IIIF</span> the
  format of a resource is also singular, whereas in the Web Annotation
  Data Model there can be more than one format.
- `language`: In <span class="abbr"
  title="International Image Interoperability Framework">IIIF</span> the
  `language` property always takes an array, whereas in the Web
  Annotation Data Model it can be a single string.
- `start`: The `start` property is used on a Manifest to refer to the
  start Canvas or part of a Canvas and thus is a <span class="abbr"
  title="JavaScript Object Notation">JSON</span> object, whereas in the
  Web Annotation Data Model it is used on a TextPositionSelector to give
  the start offset into the textual content and is thus an integer.

The `rights`, `partOf`, and `items` properties are defined by both in
the same way.

### 4.8. Keyword Mappings <a href="#48-keyword-mappings" class="anchorClass"></a>

The <span class="abbr" title="JSON for Linking Data">JSON-LD</span>
keywords `@id`, `@type` and `@none` are mapped to `id`, `type` and
`none` by the Presentation <span class="abbr"
title="Application Programming Interface">API</span> [linked data
context](/api/presentation/3.0/#46-linked-data-context-and-extensions "Linked Data Context and Extensions").
Thus in content conforming to this version of the Presentation
<span class="abbr" title="Application Programming Interface">API</span>,
the only <span class="abbr"
title="JavaScript Object Notation">JSON</span> key beginning with `@`
will be `@context`. However, the content may include data conforming to
older specifications or external specifications that use keywords
beginning with `@`. Clients should expect to encounter both syntaxes.

## 5. Resource Structure <a href="#5-resource-structure" class="anchorClass"></a>

This section provides detailed description of the resource types used in
this specification. [Section
2](/api/presentation/3.0/#2-resource-type-overview) provides an overview
of the resource types and figures illustrating allowed relationships
between them, and [Appendix
A](/api/presentation/3.0/#a-summary-of-property-requirements) provides
summary tables of the property requirements.

### 5.1. Collection <a href="#51-collection" class="anchorClass"></a>

Collections are used to list the Manifests available for viewing.
Collections *may* include both other Collections and Manifests, in order
to form a tree-structured hierarchy. Collections might align with the
curated management of cultural heritage resources in sets, also called
“collections”, but may have absolutely no such similarity.

The intended usage of Collections is to allow clients to:

- Load a pre-defined set of Manifests at initialization time.
- Receive a set of Manifests, such as search results, for rendering.
- Visualize lists or hierarchies of related Manifests.
- Provide navigation through a list or hierarchy of available Manifests.

Collections *may* be [embedded](/api/presentation/3.0/#12-terminology)
inline within other Collections, such as when the Collection is used
primarily to subdivide a larger one into more manageable pieces, however
Manifests *must not* be
[embedded](/api/presentation/3.0/#12-terminology) within Collections. An
[embedded](/api/presentation/3.0/#12-terminology) Collection *should*
also have its own URI from which the <span class="abbr"
title="JavaScript Object Notation">JSON</span> description is available.

Manifests or Collections *may* be
[referenced](/api/presentation/3.0/#12-terminology) from more than one
Collection. For example, an institution might define four Collections:
one for modern works, one for historical works, one for newspapers and
one for books. The Manifest for a modern newspaper would then appear in
both the modern Collection and the newspaper Collection. Alternatively,
the institution may choose to have two separate newspaper Collections,
and reference each as a sub-Collection of modern and historical.

Collections with an empty `items` property are allowed but discouraged.
For example, if the user performs a search that matches no Manifests,
then the server *may* return a Collection response with no Manifests.

Collections or Manifests
[referenced](/api/presentation/3.0/#12-terminology) in the `items`
property *must* have the `id`, `type` and `label` properties. They
*should* have the `thumbnail` property.

An example Collection document:

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "@context": "http://iiif.io/api/presentation/3/context.json",
  "id": "https://example.org/iiif/collection/top",
  "type": "Collection",
  "label": { "en": [ "Collection for Example Organization" ] },
  "summary": { "en": [ "Short summary of the Collection" ] },
  "requiredStatement": {
    "label": { "en": [ "Attribution" ] },
    "value": { "en": [ "Provided by Example Organization" ] }
  },

  "items": [
    {
      "id": "https://example.org/iiif/1/manifest",
      "type": "Manifest",
      "label": { "en": [ "Example Manifest 1" ] },
      "thumbnail": [
        {
          "id": "https://example.org/manifest1/thumbnail.jpg",
          "type": "Image",
          "format": "image/jpeg"
        }
      ]
    }
  ]
}
```

</div>

</div>

Note that while the Collection *may* reference Collections or Manifests
from previous versions of the <span class="abbr"
title="Application Programming Interface">API</span>, the information
included in this document *must* follow the current version
requirements, not the requirements of the target document. This is in
contrast to the requirements of `service`, as there is no way to
distinguish a version 2 Manifest from a version 3 Manifest by its
`type`.

### 5.2. Manifest <a href="#52-manifest" class="anchorClass"></a>

The Manifest resource typically represents a single object and any
intellectual work or works embodied within that object. In particular it
includes descriptive, rights and linking information for the object. The
Manifest embeds the Canvases that should be rendered as views of the
object and contains sufficient information for the client to initialize
itself and begin to display something quickly to the user.

The identifier in `id` *must* be able to be dereferenced to retrieve the
<span class="abbr" title="JavaScript Object Notation">JSON</span>
description of the Manifest, and thus *must* use the <span class="abbr"
title="Hypertext Transfer Protocol">HTTP</span>(S) URI scheme.

The Manifest *must* have an `items` property, which is an array of
<span class="abbr" title="JSON for Linking Data">JSON-LD</span> objects.
Each object is a Canvas, with requirements as described in the next
section. The Manifest *may* also have a `structures` property listing
one or more [Ranges](/api/presentation/3.0/#54-range) which describe
additional structure of the content, such as might be rendered as a
table of contents. The Manifest *may* have an `annotations` property,
which includes Annotation Page resources where the Annotations have the
Manifest as their `target`. These will typically be comment style
Annotations, and *must not* have `painting` as their `motivation`.

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  // Metadata about this manifest file
  "@context": "http://iiif.io/api/presentation/3/context.json",
  "id": "https://example.org/iiif/book1/manifest",
  "type": "Manifest",

  // Descriptive metadata about the object/work
  "label": { "en": [ "Book 1" ] },
  "metadata": [
    {
      "label": { "en": [ "Author" ] },
      "value": { "none": [ "Anne Author" ] }
    },
    {
      "label": { "en": [ "Published" ] },
      "value": {
        "en": [ "Paris, circa 1400" ],
        "fr": [ "Paris, environ 1400" ]
      }
    },
    {
      "label": { "en": [ "Notes" ] },
      "value": {
        "en": [
          "Text of note 1",
          "Text of note 2"
        ]
      }
    },
    {
      "label": { "en": [ "Source" ] },
      "value": { "none": [ "<span>From: <a href=\"https://example.org/db/1.html\">Some Collection</a></span>" ] }
    }
  ],
  "summary": { "en": [ "Book 1, written by Anne Author, published in Paris around 1400." ] },

  "thumbnail": [
    {
      "id": "https://example.org/iiif/book1/page1/full/80,100/0/default.jpg",
      "type": "Image",
      "format": "image/jpeg",
      "service": [
        {
          "id": "https://example.org/iiif/book1/page1",
          "type": "ImageService3",
          "profile": "level1"
        }
      ]
    }
  ],

  // Presentation Information
  "viewingDirection": "right-to-left",
  "behavior": [ "paged" ],
  "navDate": "1856-01-01T00:00:00Z",

  // Rights Information
  "rights": "http://creativecommons.org/licenses/by/4.0/",
  "requiredStatement": {
    "label": { "en": [ "Attribution" ] },
    "value": { "en": [ "Provided by Example Organization" ] }
  },
  "provider": [
    {
      "id": "https://example.org/about",
      "type": "Agent",
      "label": { "en": [ "Example Organization" ] },
      "homepage": [
        {
          "id": "https://example.org/",
          "type": "Text",
          "label": { "en": [ "Example Organization Homepage" ] },
          "format": "text/html"
        }
      ],
      "logo": [
        {
          "id": "https://example.org/service/inst1/full/max/0/default.png",
          "type": "Image",
          "format": "image/png",
          "service": [
            {
              "id": "https://example.org/service/inst1",
              "type": "ImageService3",
              "profile": "level2"
            }
          ]
        }
      ],
      "seeAlso": [
        {
          "id": "https://data.example.org/about/us.jsonld",
          "type": "Dataset",
          "format": "application/ld+json",
          "profile": "https://schema.org/"
        }
      ]
    }
  ],

  // Links
  "homepage": [
    {
      "id": "https://example.org/info/book1/",
      "type": "Text",
      "label": { "en": [ "Home page for Book 1" ] },
      "format": "text/html"
    }
  ],
  "service": [
    {
      "id": "https://example.org/service/example",
      "type": "ExampleExtensionService",
      "profile": "https://example.org/docs/example-service.html"
    }
  ],
  "seeAlso": [
    {
      "id": "https://example.org/library/catalog/book1.xml",
      "type": "Dataset",
      "format": "text/xml",
      "profile": "https://example.org/profiles/bibliographic"
    }
  ],
  "rendering": [
    {
      "id": "https://example.org/iiif/book1.pdf",
      "type": "Text",
      "label": { "en": [ "Download as PDF" ] },
      "format": "application/pdf"
    }
  ],
  "partOf": [
    {
      "id": "https://example.org/collections/books/",
      "type": "Collection"
    }
  ],
  "start": {
    "id": "https://example.org/iiif/book1/canvas/p2",
    "type": "Canvas"
  },

  // List of Services, referenced from within items, structures or annotations
  "services": [
    {
      "@id": "https://example.org/iiif/auth/login",
      "@type": "AuthCookieService1",
      "profile": "http://iiif.io/api/auth/1/login",
      "label": "Login to Example Institution",
      "service": [
        {
          "@id": "https://example.org/iiif/auth/token",
          "@type": "AuthTokenService1",
          "profile": "http://iiif.io/api/auth/1/token"          
        }
      ]
    }
  ],

  // List of Canvases
  "items": [
    {
      "id": "https://example.org/iiif/book1/canvas/p1",
      "type": "Canvas",
      "label": { "none": [ "p. 1" ] }
      // ...
    }
  ],

  // structure of the resource, described with Ranges
  "structures": [
    {
      "id": "https://example.org/iiif/book1/range/top",
      "type": "Range"
      // Ranges members should be included here
    }
    // Any additional top level Ranges can be included here
  ],

  // Commentary Annotations on the Manifest
  "annotations": [
    {
      "id": "https://example.org/iiif/book1/annotations/p1",
      "type": "AnnotationPage",
      "items": [
        // Annotations about the Manifest are included here
      ]
    }
  ]
}
```

</div>

</div>

### 5.3. Canvas <a href="#53-canvas" class="anchorClass"></a>

The Canvas represents an individual page or view and acts as a central
point for assembling the different content resources that make up the
display. Canvases *must* be identified by a URI and it *must* be an
<span class="abbr" title="Hypertext Transfer Protocol">HTTP</span>(S)
URI. The URI of the canvas *must not* contain a fragment (a `#` followed
by further characters), as this would make it impossible to refer to a
segment of the Canvas’s area using the [media fragment
syntax](http://www.w3.org/TR/media-frags/ "Media Fragments") of `#xywh=`
for spatial regions, and/or `#t=` for temporal segments. Canvases *may*
be able to be dereferenced separately from the Manifest via their URIs
as well as being [embedded](/api/presentation/3.0/#12-terminology).

Every Canvas *should* have a `label` to display. If one is not provided,
the client *should* automatically generate one for use based on the
Canvas’s position within the `items` property.

Content resources are associated with the Canvas via Web Annotations.
Content that is to be rendered as part of the Canvas *must* be
associated by an Annotation that has the `motivation` value `painting`.
These Annotations are recorded in the `items` of one or more Annotation
Pages, referred to in the `items` array of the Canvas. Annotations that
do not have the `motivation` value `painting` *must not* be in pages
[referenced](/api/presentation/3.0/#12-terminology) in `items`, but
instead in the `annotations` property. Referenced, external Annotation
Pages *must* have the `id` and `type` properties.

Content that is derived from the Canvas, such as a manual or automatic
(OCR) transcription of text in an image or the words spoken in an audio
representation, *must* be associated by an Annotation that has the
`motivation` value `supplementing`. Annotations *may* have any other
`motivation` values as well. Thus, content of any type may be associated
with the Canvas via an Annotation that has the `motivation` value
`painting`, meaning the content is *part of* the Canvas; an Annotation
that has the `motivation` value `supplementing`, meaning the content is
*from* the Canvas but not necessarily part of it; or an Annotation with
another `motivation` meaning that it is somehow about the Canvas.

A Canvas *must* have a rectangular aspect ratio (described with the
`height` and `width` properties) and/or a `duration` to provide an
extent in time. These dimensions allow resources to be associated with
specific regions of the Canvas, within the space and/or time extents
provided. Content *must not* be associated with space or time outside of
the Canvas’s dimensions, such as at coordinates below 0,0, greater than
the height or width, before 0 seconds, or after the duration. Content
resources that have dimensions which are not defined for the Canvas
*must not* be associated with that Canvas by an Annotation that has the
`motivation` value `painting`. For example, it is valid to use an
Annotation that has the `motivation` value `painting` to associate an
Image (which has only height and width) with a Canvas that has all three
dimensions, but it is an error to associate a Video resource (which has
height, width and duration) with a Canvas that does not have all three
dimensions. Such a resource *should* instead be
[referenced](/api/presentation/3.0/#12-terminology) using the
`rendering` property, or by Annotations that have a `motivation` value
other than `painting` in the `annotations` property.

Parts of Canvases *may* be described using a Specific Resource with a
Selector, following the patterns defined in the [Web
Annotation](http://w3.org/TR/annotation-model/ "Web Annotation Model")
data model. The use of the FragmentSelector class is *recommended* by
that specification, as it allows for refinement by other Selectors and
for consistency with use cases that cannot be represented using a URI
fragment directly. Parts of Canvases can be
[referenced](/api/presentation/3.0/#12-terminology) from Ranges, as the
`body` or `target` of Annotations, or in the `start` property.

Parts of Canvases *may* also be identified by appending a fragment to
the Canvas’s URI, and these parts are still considered to be Canvases:
their `type` value is the string `Canvas`. Rectangular spatial parts of
Canvases *may* also be described by appending an `xywh=` fragment to the
end of the Canvas’s URI. Similarly, temporal parts of Canvases *may* be
described by appending a `t=` fragment to the end of the Canvas’s URI.
Spatial and temporal fragments *may* be combined, using an `&` character
between them, and the temporal dimension *should* come first. It is an
error to select a region using a dimension that is not defined by the
Canvas, such as a temporal region of a Canvas that only has height and
width dimensions.

Canvases *may* be treated as content resources for the purposes of
annotating on to other Canvases. For example, a Canvas (Canvas A) with a
video resource and Annotations representing subtitles or captions may be
annotated on to another Canvas (Canvas B). This pattern maintains the
correct spatial and temporal alignment of Canvas A’s content relative to
Canvas B’s dimensions.

Renderers *must* scale content into the space represented by the Canvas,
and *should* follow any `timeMode` value provided for time-based media.
If the Canvas represents a view of a physical object, the spatial
dimensions of the Canvas *should* be the same scale as that physical
object, and content *should* represent only the object.

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  // Metadata about this canvas
  "id": "https://example.org/iiif/book1/canvas/p1",
  "type": "Canvas",
  "label": { "none": [ "p. 1" ] },
  "height": 1000,
  "width": 750,

  "items": [
    {
      "id": "https://example.org/iiif/book1/content/p1/1",
      "type": "AnnotationPage",
      "items": [
        // Painting Annotations on the Canvas are included here
      ]
    }
  ],

  "annotations": [
    {
      "id": "https://example.org/iiif/book1/comments/p1/1",
      "type": "AnnotationPage",
      "items": [
        // Non-Painting Annotations on the Canvas are included here
      ]
    }

  ]
}
```

</div>

</div>

### 5.4. Range <a href="#54-range" class="anchorClass"></a>

Ranges are used to represent structure within an object beyond the
default order of the Canvases in the `items` property of the Manifest,
such as newspaper sections or articles, chapters within a book, or
movements within a piece of music. Ranges can include Canvases, parts of
Canvases, or other Ranges, creating a tree structure like a table of
contents.

The intent of adding a Range to the Manifest is to allow the client to
display a linear or hierarchical navigation interface to enable the user
to quickly move through the object’s content. Clients *should* present
only Ranges that have the `label` property and do not have a `behavior`
value `no-nav` to the user. Clients *should not* render Canvas labels as
part of the navigation, and a Range that wraps the Canvas *must* be
created if this is the desired presentation.

If there is no Range that has the `behavior` value `sequence`, and the
Manifest does not have the `behavior` value `unordered`, then the client
*should* treat the order of the Canvases in the Manifest’s `items` array
as the default order. If there is one Range that has the `behavior`
value `sequence`, then the client *must* instead use this Range for the
ordering. If there is more than one Range that has the `behavior` value
`sequence`, for example a second Range to represent an alternative
ordering of the pages of a manuscript, the first Range *should* be used
as the default and the others *should* be able to be selected. Ranges
that have the `behavior` value `sequence` *must* be directly within the
`structures` property of the Manifest, and *must not* be
[embedded](/api/presentation/3.0/#12-terminology) or
[referenced](/api/presentation/3.0/#12-terminology) within other Ranges.
These Ranges may have limited hierarchical nesting, but clients are not
expected to traverse very deep structures in determining the default
order. If this Range includes parts of Canvases, then these parts are
the content to render by default and would generate separate entries in
a navigation display. This allows for the Canvas to include content
outside of the default view, such as a color bar or ruler.

Ranges *must* have URIs and they *should* be <span class="abbr"
title="Hypertext Transfer Protocol">HTTP</span>(S) URIs. Top level
Ranges are [embedded](/api/presentation/3.0/#12-terminology) or
externally [referenced](/api/presentation/3.0/#12-terminology) within
the Manifest in a `structures` property. These top level Ranges then
embed or reference other Ranges, Canvases or parts of Canvases in the
`items` property. Each entry in the `items` property *must* be a
<span class="abbr" title="JavaScript Object Notation">JSON</span>
object, and it *must* have the `id` and `type` properties. If a top
level Range needs to be dereferenced by the client, then it *must not*
have the `items` property, such that clients are able to recognize that
it should be retrieved in order to be processed.

All of the Canvases or parts that should be considered as being part of
a Range *must* be included within the Range’s `items` property, or a
descendant Range’s `items`.

The Canvases and parts of Canvases need not be contiguous or in the same
order as in the Manifest’s `items` property or any other Range. Examples
include newspaper articles that are continued in different sections, a
chapter that starts half way through a page, or time segments of a
single canvas that represent different sections of a piece of music.

Ranges *may* link to an Annotation Collection that has the content of
the Range using the `supplementary` property. The
[referenced](/api/presentation/3.0/#12-terminology) Annotation
Collection will contain Annotations that target areas of Canvases within
the Range and link content resources to those Canvases.

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "@context": "http://iiif.io/api/presentation/3/context.json",
  "id": "https://example.org/iiif/book1/manifest",
  "type": "Manifest",
  // Metadata here ...

  "items": [
    // Canvases here ...
  ],

  "structures": [
    {
      "id": "https://example.org/iiif/book1/range/r0",
      "type": "Range",
      "label": { "en": [ "Table of Contents" ] },
      "items": [
        {
          "id": "https://example.org/iiif/book1/canvas/cover",
          "type": "Canvas"
        },
        {
          "id": "https://example.org/iiif/book1/range/r1",
          "type": "Range",
          "label": { "en": [ "Introduction" ] },
          "supplementary": {
            "id": "https://example.org/iiif/book1/annocoll/introTexts",
            "type": "AnnotationCollection"
          },
          "items": [
            {
              "id": "https://example.org/iiif/book1/canvas/p1",
              "type": "Canvas"
            },
            {
              "id": "https://example.org/iiif/book1/canvas/p2",
              "type": "Canvas"
            },
            {
              "type": "SpecificResource",
              "source": "https://example.org/iiif/book1/canvas/p3",
              "selector": {
                "type": "FragmentSelector",
                "value": "xywh=0,0,750,300"
              }
            }
          ]
        },
        {
          "id": "https://example.org/iiif/book1/canvas/backCover",
          "type": "Canvas"
        }
      ]
    }
  ]
}
```

</div>

</div>

### 5.5. Annotation Page <a href="#55-annotation-page" class="anchorClass"></a>

Association of Images and other content with their respective Canvases
is done via Annotations. Traditionally Annotations are used for
associating commentary with the resource the Annotation’s text or body
is about, the [Web
Annotation](http://w3.org/TR/annotation-model/ "Web Annotation Model")
model allows any resource to be associated with any other resource, or
parts thereof, and it is reused for both commentary and painting
resources on the Canvas. Other resources beyond images might include the
full text of the object, musical notations, musical performances,
diagram transcriptions, commentary Annotations, tags, video, data and
more.

These Annotations are collected together in Annotation Page resources,
which are included in the `items` property from the Canvas. Each
Annotation Page can be [embedded](/api/presentation/3.0/#12-terminology)
in its entirety, if the Annotations should be processed as soon as
possible when the user navigates to that Canvas, or a reference to an
external page. This reference *must* include `id` and `type`, *must not*
include `items` and *may* include other properties, such as `behavior`.
All of the Annotations in the Annotation Page *should* have the Canvas
as their `target`. Clients *should* process the Annotation Pages and
their items in the order given in the Canvas. Publishers may choose to
expedite the processing of
[embedded](/api/presentation/3.0/#12-terminology) Annotation Pages by
ordering them before external pages, which will need to be dereferenced
by the client.

An Annotation Page *must* have an <span class="abbr"
title="Hypertext Transfer Protocol">HTTP</span>(S) URI given in `id`,
and *may* have any of the other properties defined in this specification
or the Web Annotation specification. The Annotations are listed in the
`items` property of the Annotation Page.

**Incompatibility Warning**\
The definition of `label` in the Web Annotation specification does not
produce <span class="abbr"
title="JavaScript Object Notation">JSON</span> conformant with the
structure defined in this specification for languages. Given the
absolute requirement for internationalized labels and the strong desire
for consistently handling properties, the `label` property on Annotation
model classes does not conform to the string requirement of the Web
Annotation Data Model. This [issue has been filed with the
W3C](https://github.com/w3c/web-annotation/issues/437) and will
hopefully be addressed in a future version of the standard.

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "@context": "http://iiif.io/api/presentation/3/context.json",
  "id": "https://example.org/iiif/book1/annopage/p1",
  "type": "AnnotationPage",

  "items": [
    {
      "id": "https://example.org/iiif/book1/annopage/p1/a1",
      "type": "Annotation"
      // ...
    },
    {
      "id": "https://example.org/iiif/book1/annopage/p1/a2",
      "type": "Annotation"
      // ...
    }
  ]
}
```

</div>

</div>

### 5.6. Annotation <a href="#56-annotation" class="anchorClass"></a>

Annotations follow the [Web
Annotation](http://w3.org/TR/annotation-model/ "Web Annotation Model")
data model. The description provided here is a summary plus any
<span class="abbr"
title="International Image Interoperability Framework">IIIF</span>
specific requirements. The W3C standard is the official documentation.

Annotations *must* have their own <span class="abbr"
title="Hypertext Transfer Protocol">HTTP</span>(S) URIs, conveyed in the
`id` property. The <span class="abbr"
title="JSON for Linking Data">JSON-LD</span> description of the
Annotation *should* be returned if the URI is dereferenced, according to
the [Web Annotation
Protocol](http://w3.org/TR/annotation-protocol/ "Web Annotation Protocol").

When Annotations are used to associate content resources with a Canvas,
the content resource is linked in the `body` of the Annotation. The URI
of the Canvas *must* be repeated in the `target` property of the
Annotation, or the `source` property of a Specific Resource used in the
`target` property.

Note that the Web Annotation data model defines different patterns for
the `value` property, when used within an Annotation. The value of a
Textual Body or a Fragment Selector, for example, are strings rather
than <span class="abbr" title="JavaScript Object Notation">JSON</span>
objects with languages and values. Care must be taken to use the correct
string form in these cases.

Additional features of the Web Annotation data model *may* also be used,
such as selecting a segment of the Canvas or content resource, or
embedding the comment or transcription within the Annotation. The use of
these advanced features sometimes results in situations where the
`target` is not a content resource, but instead a SpecificResource, a
Choice, or other non-content object. Implementations should check the
`type` of the resource and not assume that it is always content to be
rendered.

The <span class="abbr"
title="International Image Interoperability Framework">IIIF</span>
community has defined [additional Selector
classes](/api/registry/selectors/) for use with SpecificResources,
especially for cases when it is not possible to use the official
FragmentSelector. See the additional documentation for details.

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "@context": "http://iiif.io/api/presentation/3/context.json",
  "id": "https://example.org/iiif/book1/annotation/p0001-image",
  "type": "Annotation",
  "motivation": "painting",
  "body": {
    "id": "https://example.org/images/page1.jpg",
    "type": "Image"
  },
  "target": "https://example.org/iiif/book1/canvas/p1"
}
```

</div>

</div>

### 5.7. Content Resources <a href="#57-content-resources" class="anchorClass"></a>

Content resources are external web resources that are
[referenced](/api/presentation/3.0/#12-terminology) from within the
Manifest or Collection. This includes images, video, audio, data, web
pages or any other format.

As described in the [Canvas](/api/presentation/3.0/#53-canvas) section,
the content associated with a Canvas (and therefore the content of a
Manifest) is provided by the `body` property of Annotations with the
`painting` motivation. Content resources can also be
[referenced](/api/presentation/3.0/#12-terminology) from `thumbnail`,
`homepage`, `logo`, `rendering`, and `seeAlso` properties.

Content resources *must* have an `id` property, with the value being the
URI at which the resource can be obtained.

The type of the content resource *must* be included, and *should* be
taken from the table listed under the definition of `type`. The `format`
of the resource *should* be included and, if so, *should* be the media
type that is returned when the resource is dereferenced. The `profile`
of the resource, if it has one, *should* also be included. Content
resources in appropriate formats *may* also have the `language`,
`height`, `width`, and `duration` properties. Content resources *may*
also have descriptive and linking properties, as defined in [section
3](/api/presentation/3.0/#3-resource-properties).

If the content resource is an Image, and a <span class="abbr"
title="International Image Interoperability Framework">IIIF</span> Image
service is available for it, then the `id` property of the content
resource *may* be a complete URI to any particular representation
supported by the Image Service, such as
`https://example.org/image1/full/1000,/0/default.jpg`, but *must not* be
just the URI of the <span class="abbr"
title="International Image Interoperability Framework">IIIF</span> Image
service. Its `type` value *must* be the string `Image`. Its media type
*may* be listed in `format`, and its height and width *may* be given as
integer values for `height` and `width` respectively. The Image *should*
have the service [referenced](/api/presentation/3.0/#12-terminology)
from it using the `service` property.

If there is a need to distinguish between content resources, then the
resource *should* have the `label` property.

A Canvas *may* be treated as a content resource for the purposes of
annotating it on to other Canvases. In this situation, the Canvas *may*
be [embedded](/api/presentation/3.0/#12-terminology) within the
Annotation, or require dereferencing to obtain its description.

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "@context": "http://iiif.io/api/presentation/3/context.json",
  "id": "https://example.org/iiif/book1/annotation/p0001-image",
  "type": "Annotation",
  "motivation": "painting",
  "body": {
    "id": "https://example.org/iiif/book1/page1/full/max/0/default.jpg",
    "type": "Image",
    "label": { "en": [ "Page 1" ], "es": [ "Página 1" ] },
    "format": "image/jpeg",
    "service": [
      {
        "id": "https://example.org/iiif/book1/page1",
        "type": "ImageService3",
        "profile": "level2",
        "service": [
          {
            "@id": "https://example.org/iiif/auth/login",
            "@type": "AuthCookieService1"
          }
        ]
      }
    ],
    "height": 2000,
    "width": 1500
  },
  "target": "https://example.org/iiif/book1/canvas/p1"
}
```

</div>

</div>

### 5.8. Annotation Collection <a href="#58-annotation-collection" class="anchorClass"></a>

Annotation Collections represent groupings of Annotation Pages that
should be managed as a single whole, regardless of which Canvas or
resource they target. This allows, for example, all of the Annotations
that make up a particular translation of the text of a book to be
collected together. A client might then present a user interface that
allows all of the Annotations in an Annotation Collection to be
displayed or hidden according to the user’s preference.

Annotation Collections *must* have a URI, and it *should* be an
<span class="abbr" title="Hypertext Transfer Protocol">HTTP</span>(S)
URI. They *should* have a `label` and *may* have any of the other
descriptive, linking or rights properties.

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "@context": "http://iiif.io/api/presentation/3/context.json",
  "id": "https://example.org/iiif/book1/annocoll/transcription",
  "type": "AnnotationCollection",
  "label": {"en": ["Diplomatic Transcription"]},

  "first": { "id": "https://example.org/iiif/book1/annopage/l1", "type": "AnnotationPage" },
  "last": { "id": "https://example.org/iiif/book1/annopage/l120", "type": "AnnotationPage" }
}
```

</div>

</div>

For Annotation Collections with many Annotations, there will be many
pages. The Annotation Collection refers to the first and last page, and
then the pages refer to the previous and next pages in the ordered list.
Each page is part of the Annotation Collection.

<div class="code-header">

</div>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "@context": "http://iiif.io/api/presentation/3/context.json",
  "id": "https://example.org/iiif/book1/annopage/l1",
  "type": "AnnotationPage",
  "partOf": {
    "id": "https://example.org/iiif/book1/annocoll/transcription",
    "type": "AnnotationCollection"
  },
  "next": {
    "id": "https://example.org/iiif/book1/annopage/l2",
    "type": "AnnotationPage"
  },
  "items": [
    {
      "id": "https://example.org/iiif/book1/annopage/p1/a1",
      "type": "Annotation"
      // ...
    }
  ]
}
```

</div>

</div>

## 6. <span class="abbr" title="Hypertext Transfer Protocol">HTTP</span> Requests and Responses <a href="#6-http-requests-and-responses" class="anchorClass"></a>

This section describes the *recommended* request and response
interactions for the <span class="abbr"
title="Application Programming Interface">API</span>. The
<span class="abbr" title="Representational State Transfer">REST</span>
and simple <span class="abbr"
title="Hypermedia as the Engine of Application State">HATEOAS</span>
approach is followed where an interaction will retrieve a description of
the resource, and additional calls may be made by following links
obtained from within the description. All of the requests use the
<span class="abbr" title="Hypertext Transfer Protocol">HTTP</span> GET
method; creation and update of resources is not covered by this
specification. It is *recommended* that implementations also support
<span class="abbr" title="Hypertext Transfer Protocol">HTTP</span> HEAD
requests.

### 6.1. URI Recommendations <a href="#61-uri-recommendations" class="anchorClass"></a>

While any <span class="abbr"
title="Hypertext Transfer Protocol">HTTP</span>(S) URI is technically
acceptable for any of the resources in the <span class="abbr"
title="Application Programming Interface">API</span>, there are several
best practices for designing the URIs for the resources.

- The URI *should* use the <span class="abbr"
  title="Hypertext Transfer Protocol (Secure)">HTTPS</span> scheme, not
  <span class="abbr" title="Hypertext Transfer Protocol">HTTP</span>.
- The URI *should not* include query parameters or fragments.
- Once published, they *should* be as persistent and unchanging as
  possible.
- Special characters *must* be encoded.

### 6.2. Requests <a href="#62-requests" class="anchorClass"></a>

Clients are only expected to follow links to Presentation
<span class="abbr" title="Application Programming Interface">API</span>
resources. Unlike [<span class="abbr"
title="International Image Interoperability Framework">IIIF</span> Image
<span class="abbr"
title="Application Programming Interface">API</span>](/api/image/3.0/ "Image API")
requests, or other parameterized services, the URIs for Presentation
<span class="abbr" title="Application Programming Interface">API</span>
resources cannot be assumed to follow any particular pattern.

### 6.3. Responses <a href="#63-responses" class="anchorClass"></a>

The format for all responses is <span class="abbr"
title="JavaScript Object Notation">JSON</span>, as described above. It
is good practice for all resources with an <span class="abbr"
title="Hypertext Transfer Protocol">HTTP</span>(S) URI to provide their
description when the URI is dereferenced. If a resource is
[referenced](/api/presentation/3.0/#12-terminology) within a response,
rather than being [embedded](/api/presentation/3.0/#12-terminology),
then it *must* be able to be dereferenced.

If the server receives a request with an `Accept` header, it *should*
respond following the rules of [content
negotiation](https://tools.ietf.org/html/rfc7231#section-5.3.2 "HTTP 1.1, 5.3.2. Accept").
Note that content types provided in the `Accept` header of the request
*may* include parameters, for example `profile` or `charset`.

If the request does not include an `Accept` header, the
<span class="abbr" title="Hypertext Transfer Protocol">HTTP</span>
`Content-Type` header of the response *should* have the value
`application/ld+json` (<span class="abbr"
title="JSON for Linking Data">JSON-LD</span>) with the `profile`
parameter given as the context document:
`http://iiif.io/api/presentation/3/context.json`.

<div class="code-header">

</div>

<div class="language-plaintext urltemplate highlighter-rouge">

<div class="highlight">

``` highlight
Content-Type: application/ld+json;profile="http://iiif.io/api/presentation/3/context.json"
```

</div>

</div>

If the `Content-Type` header `application/ld+json` cannot be generated
due to server configuration details, then the `Content-Type` header
*should* instead be `application/json` (regular <span class="abbr"
title="JavaScript Object Notation">JSON</span>), without a `profile`
parameter.

<div class="code-header">

</div>

<div class="language-plaintext urltemplate highlighter-rouge">

<div class="highlight">

``` highlight
Content-Type: application/json
```

</div>

</div>

The <span class="abbr" title="Hypertext Transfer Protocol">HTTP</span>
server *must* follow the [<span class="abbr"
title="Cross-Origin Resource Sharing">CORS</span>
requirements](https://www.w3.org/TR/cors/ "Cross-Origin Resource Sharing")
to enable browser-based clients to retrieve the descriptions. If the
server receives a request with one of the content types above in the
Accept header, it *should* respond with that content type following the
rules of [content
negotiation](https://tools.ietf.org/html/rfc7231#section-5.3.2 "HTTP 1.1, 5.3.2. Accept").
Recipes for enabling <span class="abbr"
title="Cross-Origin Resource Sharing">CORS</span> and conditional
Content-Type headers are provided in the [Apache <span class="abbr"
title="Hypertext Transfer Protocol">HTTP</span> Server Implementation
Notes](/api/annex/notes/apache/ "Apache HTTP Server Implementation Notes").

Responses *should* be compressed by the server as there are significant
performance gains to be made for very repetitive data structures.

## 7. Authentication <a href="#7-authentication" class="anchorClass"></a>

It may be necessary to restrict access to the descriptions made
available via the Presentation <span class="abbr"
title="Application Programming Interface">API</span>. As the primary
means of interaction with the descriptions is by web browsers using
XmlHttpRequests across domains, there are some considerations regarding
the most appropriate methods for authenticating users and authorizing
their access. The approach taken is described in the
[Authentication](/api/auth/ "IIIF Authentication API") specification,
and requires requesting a token to add to the requests to identify the
user. This token might also be used for other requests defined by other
APIs.

It is possible to include Image <span class="abbr"
title="Application Programming Interface">API</span> service
descriptions within the Manifest, and within those it is also possible
to include links to the Authentication <span class="abbr"
title="Application Programming Interface">API</span>’s services that are
needed to interact with the image content. The first time an
Authentication <span class="abbr"
title="Application Programming Interface">API</span> service is included
within a Manifest, it *must* be the complete description. Subsequent
references *should* be just the URI of the service, and clients are
expected to look up the details from the full description by matching
the URI. Clients *must* anticipate situations where the Authentication
service description in the Manifest is out of date: the source of truth
is the Image Information document, or other system that references the
Authentication <span class="abbr"
title="Application Programming Interface">API</span> services.

## Appendices <a href="#appendices" class="anchorClass"></a>

### A. Summary of Property Requirements <a href="#a-summary-of-property-requirements" class="anchorClass"></a>

| Icon | Meaning |
|----|----|
| ![required](/api/assets/images/icons/required.png "Required") | Required |
| ![recommended](/api/assets/images/icons/recommended.png "Recommended") | Recommended |
| ![optional](/api/assets/images/icons/optional.png "Optional") | Optional |
| ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | Not Allowed |

**Descriptive and Rights Properties**

|   | label | metadata | summary | requiredStatement | rights | navDate | language |
|----|----|----|----|----|----|----|----|
| Collection | ![required](/api/assets/images/icons/required.png "Required") | ![recommended](/api/assets/images/icons/recommended.png "Recommended") | ![recommended](/api/assets/images/icons/recommended.png "Recommended") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") |
| Manifest | ![required](/api/assets/images/icons/required.png "Required") | ![recommended](/api/assets/images/icons/recommended.png "Recommended") | ![recommended](/api/assets/images/icons/recommended.png "Recommended") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") |
| Canvas | ![recommended](/api/assets/images/icons/recommended.png "Recommended") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") |
| Annotation | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") |
| AnnotationPage | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") |
| Range | ![recommended](/api/assets/images/icons/recommended.png "Recommended") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") |
| AnnotationCollection | ![recommended](/api/assets/images/icons/recommended.png "Recommended") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") |
| Content Resources | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![recommended](/api/assets/images/icons/recommended.png "Recommended") |

|   | provider | thumbnail | placeholderCanvas | accompanyingCanvas |
|----|----|----|----|----|
| Collection | ![recommended](/api/assets/images/icons/recommended.png "Recommended") | ![recommended](/api/assets/images/icons/recommended.png "Recommended") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") |
| Manifest | ![recommended](/api/assets/images/icons/recommended.png "Recommended") | ![recommended](/api/assets/images/icons/recommended.png "Recommended") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") |
| Canvas | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional")\* | ![optional](/api/assets/images/icons/optional.png "Optional")\* |
| Annotation | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") |
| AnnotationPage | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") |
| Range | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") |
| AnnotationCollection | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") |
| Content Resources | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") |

\*A Canvas that is the value of a `placeholderCanvas` or
`accompanyingCanvas` property may not have either of those properties
itself.\

**Technical Properties**

|   | id | type | format | profile | height | width | duration | viewingDirection | behavior | timeMode |
|----|----|----|----|----|----|----|----|----|----|----|
| Collection | ![required](/api/assets/images/icons/required.png "Required") | ![required](/api/assets/images/icons/required.png "Required") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") |
| Manifest | ![required](/api/assets/images/icons/required.png "Required") | ![required](/api/assets/images/icons/required.png "Required") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") |
| Canvas | ![required](/api/assets/images/icons/required.png "Required") | ![required](/api/assets/images/icons/required.png "Required") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![optional](/api/assets/images/icons/optional.png "Optional")\* | ![optional](/api/assets/images/icons/optional.png "Optional")\* | ![optional](/api/assets/images/icons/optional.png "Optional") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") |
| Annotation | ![required](/api/assets/images/icons/required.png "Required") | ![required](/api/assets/images/icons/required.png "Required") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") |
| Annotation Page | ![required](/api/assets/images/icons/required.png "Required") | ![required](/api/assets/images/icons/required.png "Required") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") |
| Range | ![required](/api/assets/images/icons/required.png "Required") | ![required](/api/assets/images/icons/required.png "Required") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") |
| Annotation Collection | ![required](/api/assets/images/icons/required.png "Required") | ![required](/api/assets/images/icons/required.png "Required") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") |
| Content Resources | ![required](/api/assets/images/icons/required.png "Required") | ![required](/api/assets/images/icons/required.png "Required") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") |

\*If a Canvas has either of `height` and `width`, it *must* have the
other, as described in the
[definitions](/api/presentation/3.0/#height "height property") of those
properties.\

**Linking Properties**

|   | seeAlso | service | homepage | rendering | partOf | start | supplementary | services |
|----|----|----|----|----|----|----|----|----|
| Collection | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![optional](/api/assets/images/icons/optional.png "Optional") |
| Manifest | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![optional](/api/assets/images/icons/optional.png "Optional") |
| Canvas | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") |
| Annotation | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") |
| Annotation Page | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") |
| Range | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") |
| Annotation Collection | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") |
| Content Resources | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") |

**Structural Properties**

|   | items | structures | annotations |
|----|----|----|----|
| Collection | ![required](/api/assets/images/icons/required.png "Required") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![optional](/api/assets/images/icons/optional.png "Optional") |
| Manifest | ![required](/api/assets/images/icons/required.png "Required") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") |
| Canvas | ![recommended](/api/assets/images/icons/recommended.png "Recommended") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![optional](/api/assets/images/icons/optional.png "Optional") |
| Annotation | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") |
| Annotation Page | ![recommended](/api/assets/images/icons/recommended.png "Recommended") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") |
| Range | ![required](/api/assets/images/icons/required.png "Required") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![optional](/api/assets/images/icons/optional.png "Optional") |
| Annotation Collection | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") |
| Content Resources | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![optional](/api/assets/images/icons/optional.png "Optional") |

**Behavior Values**

|   | Collection | Manifest | Canvas | Range |
|----|----|----|----|----|
| auto-advance | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") |
| continuous | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![optional](/api/assets/images/icons/optional.png "Optional") |
| facing-pages | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") |
| individuals | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![optional](/api/assets/images/icons/optional.png "Optional") |
| multi-part | ![optional](/api/assets/images/icons/optional.png "Optional") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") |
| no-auto-advance | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") |
| no-nav | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![optional](/api/assets/images/icons/optional.png "Optional") |
| no-repeat | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") |
| non-paged | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") |
| hidden \* | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") |
| paged | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![optional](/api/assets/images/icons/optional.png "Optional") |
| repeat | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") |
| sequence | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![optional](/api/assets/images/icons/optional.png "Optional") |
| thumbnail-nav | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![optional](/api/assets/images/icons/optional.png "Optional") |
| together | ![optional](/api/assets/images/icons/optional.png "Optional") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") |
| unordered | ![optional](/api/assets/images/icons/optional.png "Optional") | ![optional](/api/assets/images/icons/optional.png "Optional") | ![not allowed](/api/assets/images/icons/not_allowed.png "Not allowed") | ![optional](/api/assets/images/icons/optional.png "Optional") |

\* `hidden` is allowed on Annotation Collections, Annotation Pages,
Annotations, Specific Resources and Choices, as these are the classes
that result in rendering content to the user.

### B. Example Manifest Response <a href="#b-example-manifest-response" class="anchorClass"></a>

<div class="code-header">

</div>

<div class="language-json highlighter-rouge">

<div class="highlight">

``` highlight
{
  "@context": "http://iiif.io/api/presentation/3/context.json",
  "id": "https://example.org/iiif/book1/manifest",
  "type": "Manifest",
  "label": { "en": [ "Book 1" ] },
  "metadata": [
    {
      "label": { "en": [ "Author" ] },
      "value": { "none": [ "Anne Author" ] }
    },
    {
      "label": { "en": [ "Published" ] },
      "value": {
        "en": [ "Paris, circa 1400" ],
        "fr": [ "Paris, environ 1400" ]
      }
    },
    {
      "label": { "en": [ "Notes" ] },
      "value": {
        "en": [
          "Text of note 1",
          "Text of note 2"
        ]
      }
    },
    {
      "label": { "en": [ "Source" ] },
      "value": { "none": [ "<span>From: <a href=\"https://example.org/db/1.html\">Some Collection</a></span>" ] }
    }
  ],
  "summary": { "en": [ "Book 1, written be Anne Author, published in Paris around 1400." ] },

  "thumbnail": [
    {
      "id": "https://example.org/iiif/book1/page1/full/80,100/0/default.jpg",
      "type": "Image",
      "format": "image/jpeg",
      "service": [
        {
          "id": "https://example.org/iiif/book1/page1",
          "type": "ImageService3",
          "profile": "level1"
        }
      ]
    }
  ],

  "viewingDirection": "right-to-left",
  "behavior": [ "paged" ],
  "navDate": "1856-01-01T00:00:00Z",

  "rights": "https://creativecommons.org/licenses/by/4.0/",
  "requiredStatement": {
    "label": { "en": [ "Attribution" ] },
    "value": { "en": [ "Provided by Example Organization" ] }
  },

  "provider": [
      {
        "id": "https://example.org/about",
        "type": "Agent",
        "label": { "en": [ "Example Organization" ] },
        "homepage": [
          {
            "id": "https://example.org/",
            "type": "Text",
            "label": { "en": [ "Example Organization Homepage" ] },
            "format": "text/html"
          }
        ],
        "logo": [
          {
            "id": "https://example.org/service/inst1/full/max/0/default.png",
            "type": "Image",
            "format": "image/png",
            "service": [
              {
                "id": "https://example.org/service/inst1",
                "type": "ImageService3",
                "profile": "level2"
              }
            ]
          }
        ],
        "seeAlso": [
          {
            "id": "https://data.example.org/about/us.jsonld",
            "type": "Dataset",
            "format": "application/ld+json",
            "profile": "https://schema.org/"
          }
        ]
      }
    ],
  "homepage": [
    {
      "id": "https://example.org/info/book1/",
      "type": "Text",
      "label": { "en": [ "Home page for Book 1" ] },
      "format": "text/html"
    }
  ],
  "service": [
    {
      "id": "https://example.org/service/example",
      "type": "ExampleExtensionService",
      "profile": "https://example.org/docs/example-service.html"
    }
  ],
  "seeAlso": [
    {
      "id": "https://example.org/library/catalog/book1.xml",
      "type": "Dataset",
      "format": "text/xml",
      "profile": "https://example.org/profiles/bibliographic"
    }
  ],
  "rendering": [
    {
      "id": "https://example.org/iiif/book1.pdf",
      "type": "Text",
      "label": { "en": [ "Download as PDF" ] },
      "format": "application/pdf"
    }
  ],
  "partOf": [
    {
      "id": "https://example.org/collections/books/",
      "type": "Collection"
    }
  ],
  "start": {
    "id": "https://example.org/iiif/book1/canvas/p2",
    "type": "Canvas"
  },

  "services": [
    {
      "@id": "https://example.org/iiif/auth/login",
      "@type": "AuthCookieService1",
      "profile": "http://iiif.io/api/auth/1/login",
      "label": "Login to Example Institution",
      "service": [
        {
          "@id": "https://example.org/iiif/auth/token",
          "@type": "AuthTokenService1",
          "profile": "http://iiif.io/api/auth/1/token"          
        }
      ]
    }
  ],

  "items": [
    {
      "id": "https://example.org/iiif/book1/canvas/p1",
      "type": "Canvas",
      "label": { "none": [ "p. 1" ] },
      "height": 1000,
      "width": 750,
      "items": [
        {
          "id": "https://example.org/iiif/book1/page/p1/1",
          "type": "AnnotationPage",
          "items": [
            {
              "id": "https://example.org/iiif/book1/annotation/p0001-image",
              "type": "Annotation",
              "motivation": "painting",
              "body": {
                "id": "https://example.org/iiif/book1/page1/full/max/0/default.jpg",
                "type": "Image",
                "format": "image/jpeg",
                "service": [
                  {
                    "id": "https://example.org/iiif/book1/page1",
                    "type": "ImageService3",
                    "profile": "level2",
                    "service": [
                      {
                        "@id": "https://example.org/iiif/auth/login",
                        "@type": "AuthCookieService1"
                      }
                    ]
                  }
                ],
                "height": 2000,
                "width": 1500
              },
              "target": "https://example.org/iiif/book1/canvas/p1"
            }
          ]
        }
      ],
      "annotations": [
        {
          "id": "https://example.org/iiif/book1/comments/p1/1",
          "type": "AnnotationPage"
        }
      ]
    },
    {
      "id": "https://example.org/iiif/book1/canvas/p2",
      "type": "Canvas",
      "label": { "none": [ "p. 2" ] },
      "height": 1000,
      "width": 750,
      "items": [
        {
          "id": "https://example.org/iiif/book1/page/p2/1",
          "type": "AnnotationPage",
          "items": [
            {
              "id": "https://example.org/iiif/book1/annotation/p0002-image",
              "type": "Annotation",
              "motivation": "painting",
              "body": {
                "id": "https://example.org/iiif/book1/page2/full/max/0/default.jpg",
                "type": "Image",
                "format": "image/jpeg",
                "service": [
                  {
                    "id": "https://example.org/iiif/book1/page2",
                    "type": "ImageService3",
                    "profile": "level2"
                  }
                ],
                "height": 2000,
                "width": 1500
              },
              "target": "https://example.org/iiif/book1/canvas/p2"
            }
          ]
        }
      ]
    }
  ],

  "structures": [
    {
      "id": "https://example.org/iiif/book1/range/r0",
      "type": "Range",
      "label": { "en": [ "Table of Contents" ] },
      "items": [
        {
          "id": "https://example.org/iiif/book1/range/r1",
          "type": "Range",
          "label": { "en": [ "Introduction" ] },
          "supplementary": {
            "id": "https://example.org/iiif/book1/annocoll/introTexts",
            "type": "AnnotationCollection"
          },
          "items": [
            {
              "id": "https://example.org/iiif/book1/canvas/p1",
              "type": "Canvas"
            },
            {
              "type": "SpecificResource",
              "source": "https://example.org/iiif/book1/canvas/p2",
              "selector": {
                "type": "FragmentSelector",
                "value": "xywh=0,0,750,300"
              }
            }
          ]
        }
      ]
    }
  ],

  "annotations": [
    {
      "id": "https://example.org/iiif/book1/page/manifest/1",
      "type": "AnnotationPage",
      "items": [
        {
          "id": "https://example.org/iiif/book1/page/manifest/a1",
          "type": "Annotation",
          "motivation": "commenting",
          "body": {
            "type": "TextualBody",
            "language": "en",
            "value": "I love this manifest!"
          },
          "target": "https://example.org/iiif/book1/manifest"
        }
      ]
    }
  ]
}
```

</div>

</div>

### C. Versioning <a href="#c-versioning" class="anchorClass"></a>

Starting with version 2.0, this specification follows [Semantic
Versioning](http://semver.org/spec/v2.0.0.html "Semantic Versioning 2.0.0").
See the note [Versioning of
APIs](/api/annex/notes/semver/ "Versioning of APIs") for details
regarding how this is implemented.

### D. Acknowledgements <a href="#d-acknowledgements" class="anchorClass"></a>

Many thanks to the members of the [<span class="abbr"
title="International Image Interoperability Framework">IIIF</span>
community](https://iiif.io/community/ "IIIF Community") for their
continuous engagement, innovative ideas, and feedback.

Many of the changes in this version are due to the work of the
[<span class="abbr"
title="International Image Interoperability Framework">IIIF</span> AV
Technical Specification
Group](https://iiif.io/community/groups/av/ "IIIF A/V Working Group"),
chaired by Jason Ronallo (North Carolina State University), Jon Dunn
(Indiana University) and Tom Crane (Digirati). The <span class="abbr"
title="International Image Interoperability Framework">IIIF</span>
Community thanks them for their leadership, and the members of the group
for their tireless work.

### E. Change Log <a href="#e-change-log" class="anchorClass"></a>

| Date | Description |
|----|----|
| 2020-06-03 | Version 3.0 (Surfing Raven) [View change log](/api/presentation/3.0/change-log/ "Presentation API 3.0 Change Log") |
| 2017-06-09 | Version 2.1.1 [View change log](/api/presentation/2.1/change-log-211/ "Presentation API 2.1.1 Change Log") |
| 2016-05-12 | Version 2.1 (Hinty McHintface) [View change log](/api/presentation/2.1/change-log/ "Presentation API 2.1 Change Log") |
| 2014-09-11 | Version 2.0 (Triumphant Giraffe) [View change log](/api/presentation/2.0/change-log/ "Presentation API 2.0 Change Log") |
| 2013-08-26 | Version 1.0 (unnamed) |
| 2013-06-14 | Version 0.9 (unnamed) |

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
