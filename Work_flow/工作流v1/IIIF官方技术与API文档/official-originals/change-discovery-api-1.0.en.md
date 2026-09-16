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

# IIIF Change Discovery API 1.0

</div>

</div>

</div>

<div id="main" class="section">

<div class="container-block no-padding is-max-desktop">

<div class="columns is-max-desktop">

<div class="aside column is-one-quarter api-sidebar-container"
data-markdown="1">

<div class="toc-sidebar sticky">

- [1. Introduction](#introduction)
  - [1.1. Objectives and Scope](#objectives-and-scope)
  - [1.2. Terminology](#terminology)
- [2. Overview of IIIF Resource
  Discovery](#overview-of-iiif-resource-discovery)
  - [2.1. IIIF Resources and their
    Changes](#resources-and-their-changes)
  - [2.2. Pages of Changes](#pages-of-changes)
  - [2.3. Collections of Pages](#collections-of-pages)
  - [2.4. Registries of Collections](#24-registries-of-collections)
- [3. Activity Streams Details](#activity-streams-details)
  - [3.1. Ordered Collection](#orderedcollection)
  - [3.2. Ordered Collection Page](#ordered-collection-page)
  - [3.3. Activities](#activities)
  - [3.4. Linked Data Context and
    Extensions](#34-linked-data-context-and-extensions)
  - [3.5. Activity Streams Processing
    Algorithm](#activity-streams-processing-algorithm)
- [4. Network Considerations](#4-network-considerations)
  - [4.1. Media Type](#41-media-type)
  - [4.2. Activities for Access-Restricted
    Content](#42-activities-for-access-restricted-content)
  - [4.3. Negotiable Resources](#43-negotiable-resources)
- [Appendices](#appendices)
  - [A. Acknowledgements](#acknowledgements)
  - [B. Change Log](#change-log)

</div>

</div>

<div class="column is-three-quarters content api-content"
data-markdown="1">

## Status of this Document <a href="#status-of-this-document" class="anchorClass"></a>

**This Version:** 1.0.0

**Latest Stable Version:**
[1.0.0](/api/discovery/1.0/ "IIIF Change Discovery API")

**Previous Version:**
[0.9.2](/api/discovery/0.9/ "IIIF Change Discovery API")

**Editors**

- **[Michael Appleby](https://orcid.org/0000-0002-1266-298X)**, Yale
  University

- **[Tom Crane](https://orcid.org/0000-0003-1881-243X)**, Digirati

- **[Robert Sanderson](https://orcid.org/0000-0003-4441-6852)**, J. Paul
  Getty Trust

- **[Jon Stroop](https://orcid.org/0000-0002-0367-1243)**, Princeton
  University Library

- **[Simeon Warner](https://orcid.org/0000-0002-7970-7855)**, Cornell
  University

*Copyright © 2012-2026 Editors and contributors. Published by the IIIF
Consortium under the
[CC-BY](http://creativecommons.org/licenses/by/4.0/ "Creative Commons — Attribution 4.0 International")
license, see [disclaimer](/api/annex/notes/disclaimer/).*

------------------------------------------------------------------------

## 1. Introduction <a href="#introduction" class="anchorClass"></a>

The resources made available via the IIIF (pronounced “Triple-Eye-Eff”)
[Image](/api/image/3.0/ "Image API") and
[Presentation](/api/presentation/ "IIIF Presentation API") APIs are
useful only if they can be found. Users cannot interact directly with a
distributed, decentralized ecosystem but instead must rely on services
that harvest and process the available content, and then provide a user
interface enabling navigation to that content via searching, browsing or
other paradigms. Once the user has discovered the content, they can then
display it in their viewing application of choice. Machine to machine
interfaces are also enabled by this approach, where software agents can
interact via APIs to discover the same content and retrieve it for
further analysis or processing.

This specification leverages existing techniques, specifications, and
tools in order to promote widespread adoption of an easy-to-implement
service. The service describes changes to IIIF content resources and the
location of those resources to harvest. Content providers can implement
this API to enable the collaborative development of global or thematic
search engines and portal applications that ultimately allow users to
easily find and engage with content available via existing IIIF APIs.

### 1.1. Objectives and Scope <a href="#objectives-and-scope" class="anchorClass"></a>

The objective of the IIIF Change Discovery API is to provide a machine
to machine API that provides the information needed to discover and
subsequently make use of IIIF resources. The intended audience is other
IIIF-aware systems that can leverage the content and APIs. While this
work may benefit others outside of the IIIF community directly or
indirectly, the objective of the API is to specify an interoperable
solution that best and most easily fulfills the discovery needs within
the community of participating organizations.

The discovery of IIIF resources requires a consistent and well
understood pattern for content providers to publish lists of links to
their available content. This allows a baseline implementation of
discovery systems that process the list, looking for resources that have
been added or changed.

This process can be optimized by allowing the content providers to
publish descriptions of how their content has changed, enabling
consuming systems to retrieve only the resources that have been modified
since they were last retrieved. These changes might include when content
is deleted or otherwise becomes unavailable. Finally, for rapid
synchronization, a system of notifications pushed from the publisher to
a set of subscribers can reduce the amount of effort required to
constantly poll multiple sources to see if anything has changed.

Work that is out of scope of this API includes the recommendation or
creation of any descriptive metadata formats, and the recommendation or
creation of metadata search APIs or protocols. The diverse domains
represented within the IIIF community already have successful standards
fulfilling these use cases. Also out of scope is optimization of the
transmission of content, for example recommendations about transferring
any source media or data between systems.

**Change Notifications**\
This specification does not include a subscription mechanism for
enabling change notifications to be pushed to remote systems. Only
periodic polling for the set of changes that must be processed is
supported. A subscription/notification pattern may be added in a future
version after implementation experience with the polling pattern has
demonstrated that it would be valuable.

### 1.2. Terminology <a href="#terminology" class="anchorClass"></a>

The specification uses the following terms:

- **HTTP(S)**: The HTTP or HTTPS URI scheme and internet protocol.

The terms *array*, *JSON object*, *number*, and *string* in this
document are to be interpreted as defined by the [Javascript Object
Notation (JSON)](https://tools.ietf.org/html/rfc8259 "JSON RFC")
specification.

The key words *must*, *must not*, *required*, *shall*, *shall not*,
*should*, *should not*, *recommended*, *may*, and *optional* in this
document are to be interpreted as described in [RFC
2119](https://tools.ietf.org/html/rfc2119 "RFC Keywords").

## 2. Overview of IIIF Resource Discovery <a href="#overview-of-iiif-resource-discovery" class="anchorClass"></a>

In order to discover IIIF resources, the state of those resources in the
systems that publish them needs to be communicated succinctly and easily
to a consuming system. The consuming system can then use that
information to retrieve and process the resources of interest and
provide platforms that enable discovery and use. This communication
takes place via the IIIF Change Discovery API, which uses the W3C
[Activity Streams](https://www.w3.org/TR/activitystreams-core/)
specification to describe and serialize changes to resources. The
conceptual model for those changes and the interactions between
publishers and consumers are based on those identified by the
[ResourceSync](https://openarchives.org/rs/toc) framework. It is not
necessary to understand either of these standards in order to use or
implement the IIIF Change Discovery API, which is fully specified in
this document.

Activities are used to describe the state of the publishing system by
recording each individual change, in the order that they occur. The
changes described are the creation, modification and deletion of IIIF
Presentation API resources. A consuming application that is aware of all
of the changes that took place in the publishing system has full
knowledge of the set of resources available. IIIF
[Collections](/api/presentation/3.0/#overview-collection "Presentation API 3.0 Collection Type")
and
[Manifests](/api/presentation/3.0/#overview-manifest "Presentation API 3.0 Manifest Type")
are the main access points to published content and references to
descriptive metadata about that content, however, Activities describing
changes to other resources, such as the IIIF Image API endpoints or the
descriptive metadata about the object represented, could also be
published in this way. As the intended use is to inform a consuming
system, rather than to display information, the Change Discovery API
does not include any content intended to be rendered to end users.

The Presentation API does not include descriptive metadata fields, and
intentionally lacks the semantics needed to implement advanced or
fielded search. Instead, the Presentation API uses the
[`seeAlso`](/api/presentation/3.0/#seealso "seeAlso property") property
to link to external documents that can have richer and domain-specific
information about the content being presented. For example, a museum
object might have a `seeAlso` reference to a CIDOC-CRM or LIDO
description, while a bibliographic resource might reference a Dublin
Core or MODS description. These external descriptions should be used
when possible to provide interfaces giving access to more precise
matching algorithms.

This specification describes three levels of conformance that build upon
each other in terms of functionality and precision of the information
published. Sets of changes are published in pages, which are then
aggregated into a collection per publisher. To reduce barriers to entry,
care has been taken to allow for the possibility of implementing all
levels using only static files on a web server, rather than requiring
dynamic access to a database.

### 2.1. IIIF Resources and their Changes <a href="#resources-and-their-changes" class="anchorClass"></a>

There are three levels of conformance at which changes to IIIF resources
can be described. Level 0 is simply a list of the resources available.
Level 1 adds timestamps and ordering from earliest change to most
recent, allowing a consuming application to work backwards through the
list and stop processing once it encounters a change that it has already
seen from a previous run. Level 2 adds information about the types of
activities, enabling the explicit description of the creation and
deletion of resources.

The subsections below describe first how to construct the description of
the changes for each level, and then in the next section how to embed
them into ordered lists.

#### 2.1.1. Level 0: Resource References <a href="#level-0-basic-resource-list" class="anchorClass"></a>

The core information required to provide a minimally effective set of
links to IIIF resources is the URIs of those resources. The order of the
resources in the resulting list is unimportant, but each *should* only
appear once. This is the minimum level for any effective
interoperability.

This minimal level 0 API approach is compatible with the levels 1 and 2
which introduce significant benefits that allow clients to better
optimize their interactions.

If resources are deleted after being referred to in the resource list,
the entire list should be republished without the reference to the
deleted resource. Clients should also expect to encounter resource URIs
that are out of date and no longer resolve to a IIIF Manifest or
Collection, as well as activities which do not refer to IIIF resource
types at all.

Example Level 0 Activity:

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "type": "Update",
  "object": {
    "id": "https://example.org/iiif/1/manifest",
    "type": "Manifest"
  }
}
```

</div>

</div>

#### 2.1.2. Level 1: Resource Changes <a href="#level-1-basic-change-list" class="anchorClass"></a>

When dealing with large lists of resources, it can be useful to work
with only those resources that have changed since the last time the list
was processed. This is managed by the addition of a time stamp in the
`endTime` property, that indicates the time at which the resource was
last modified or initially created. Lists *must* be ordered such that
the most recent activities occur last. Consumers will then process the
list of Activities in reverse order, from last to first, stopping when
they encounter an Activity they have already processed.

Example Level 1 Activity:

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "type": "Update",
  "object": {
    "id": "https://example.org/iiif/1/manifest",
    "type": "Manifest"
  },
  "endTime": "2017-09-20T00:00:00Z"
}
```

</div>

</div>

#### 2.1.3. Level 2: Resource Creation, Change, Deletion and Moving <a href="#level-2-complete-change-list" class="anchorClass"></a>

At the most detailed level, a log of all Activities that have taken
place can be recorded, with the likelihood of multiple Activities per
IIIF resource. Use of the additional types of “Create”, “Delete” and
“Move” allows explicit description of creations, deletions and moves,
enabling a synchronization process to remove resources as well as add or
update them.

A complete change history is not required, and sometimes not even
desirable. If there are many or frequent changes to a resource, an
implementation *may* omit any number of individual changes, but *should*
always have the most recent change included in the list. Changes that
are deemed to be insignificant to the publisher of the list *may* also
be omitted, such as changes that do not affect the content visible to
users.

Example Level 2 Activity:

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "type": "Create",
  "object": {
    "id": "https://example.org/iiif/1/manifest",
    "type": "Manifest"
  },
  "endTime": "2017-09-20T00:00:00Z"
}
```

</div>

</div>

#### 2.1.4. Aggregating Activities <a href="#aggregated-activity-streams" class="anchorClass"></a>

Activities can be added to or removed at times other than when the
resources they refer to are created, modified, deleted or moved. There
are several use cases for this pattern, however they are all outside of
the normal publication of a stream by the content owners and thus are
unlikely to affect most publishing implementations. They do affect
consuming applications, and the implications are documented in [3.5.
Activity Streams Processing
Algorithm](/api/discovery/1.0/#activity-streams-processing-algorithm "Activity Streams Processing Algorithm").

The first use case is when third-party aggregators add activities
harvested from different institutions, filter those activities or
objects, and aggregate them into a composite stream. For example, a
dinosaur aggregator might filter several natural history museum streams
for only those manifests that are about dinosaurs.

Secondly, resources might become available or unavailable without being
created or deleted. This could happen because of changes to their
permissions, such as an embargo period after creation, or when resources
are temporarily removed in order to be edited as part of some data
cleaning or migration process.

Whenever an “Add” Activity is encountered, it is semantically similar to
a “Create” Activity in that it is the first time that resource is
mentioned in the stream. It is, therefore, expected that if there is an
“Add”, then there may not be a “Create” for the same resource occurring
before it. Similarly, there will be no more references to the resource
after a “Remove” or “Delete”.

Example Add Activity:

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "type": "Add",
  "summary": "Added newly discovered manifest to stream",
  "object": {
    "id": "https://example.org/iiif/1/manifest",
    "type": "Manifest"
  },
  "target": {
    "id": "https://example.org/activity/aggregated-changes",
    "type": "OrderedCollection"
  },
  "endTime": "2019-11-22T00:00:00Z"
}
```

</div>

</div>

Example Remove Activity:

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "type": "Remove",
  "summary": "Removed manifest from stream due to being out of scope",
  "object": {
    "id": "https://example.org/iiif/1/manifest",
    "type": "Manifest"
  },
  "origin": {
    "id": "https://example.org/activity/aggregated-changes",
    "type": "OrderedCollection"
  },
  "endTime": "2017-11-23T00:00:00Z"
}
```

</div>

</div>

#### 2.1.5. State Refresh Activities <a href="#state-refresh-activities" class="anchorClass"></a>

Sometimes a publishing system will do a complete refresh of its records
and re-issue an activity for every resource. When this happens, it is a
good practice to include a `Refresh` activity immediately before the
`Update` activities for the resources. This allows a consuming
application to stop looking for new resources beyond this point, as all
of the available ones will already have been encountered. Note that the
`Refresh` uses `startTime` rather than `endTime` as the datetime when it
occurs, in order to ensure that it is positioned before the resource
activities in the sorted stream.

Consuming applications that have processed the stream previously should
continue to read backwards beyond this point, in order to process any
Delete activities, but do not need to process other activity types.
Applications that have not processed the stream previously can simply
stop when the `Refresh` activity is encountered.

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "type": "Refresh",
  "summary": "System refresh initiated",
  "startTime": "2020-06-21T00:00:00Z"
}
```

</div>

</div>

### 2.2. Pages of Changes <a href="#pages-of-changes" class="anchorClass"></a>

The Activities are collected together into pages that together make up
the entire set of changes that the publishing system is aware of. Pages
reference the previous and next pages in that set, and the overall
collection of which they are part. The Activities within the page are
listed such that the most recent activities occur last.

Pages are subsequently collected together in ordered collections,
described in the following section.

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "@context": "http://iiif.io/api/discovery/1/context.json",
  "id": "https://example.org/activity/page-1",
  "type": "OrderedCollectionPage",
  "partOf": {
    "id": "https://example.org/activity/all-changes",
    "type": "OrderedCollection"
  },
  "prev": {
    "id": "https://example.org/activity/page-0",
    "type": "OrderedCollectionPage"
  },
  "next": {
    "id": "https://example.org/activity/page-2",
    "type": "OrderedCollectionPage"
  },
  "orderedItems": [
    {
      "type": "Update",
      "object": {
        "id": "https://example.org/iiif/9/manifest",
        "type": "Manifest"
      },
      "endTime": "2018-03-10T10:00:00Z"
    },
    {
      "type": "Update",
      "object": {
        "id": "https://example.org/iiif/2/manifest",
        "type": "Manifest"
      },
      "endTime": "2018-03-11T16:30:00Z"
    }
  ]
}
```

</div>

</div>

### 2.3. Collections of Pages <a href="#collections-of-pages" class="anchorClass"></a>

As the number of Activities is likely too many to usefully be
represented in a single Page, they are collected together into a
Collection as the initial entry point. The Collection references the
URIs of the first and last pages, where the first page contains the
earliest activities and the last page contains the most recent.

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "@context": "http://iiif.io/api/discovery/1/context.json",
  "id": "https://example.org/activity/all-changes",
  "type": "OrderedCollection",
  "totalItems": 21456,
  "first": {
    "id": "https://example.org/activity/page-0",
    "type": "OrderedCollectionPage"
  },
  "last": {
    "id": "https://example.org/activity/page-214",
    "type": "OrderedCollectionPage"
  }
}
```

</div>

</div>

### 2.4. Registries of Collections <a href="#24-registries-of-collections" class="anchorClass"></a>

In order to discover the URIs for Collections, and through them the URIs
of the IIIF resources, the IIIF Consortium manages a [Registry of
Collections](https://registry.iiif.io/ "IIIF Change Discovery Registry").
This registry is itself an implementation of the Change Discovery API,
however the IIIF resources are not Presentation API resources, but other
Change Discovery API resources. This might include both Collections of
Manifests, or other registries of Collections. The registry describes
how it is managed and how to retrieve or submit content. The registry
may also reference other methods of discovering IIIF content.

## 3. Activity Streams Details <a href="#activity-streams-details" class="anchorClass"></a>

The W3C [Activity Streams](https://www.w3.org/TR/activitystreams-core/)
specification defines a “model for representing potential and completed
activities”, and is compatible with the [design
patterns](/api/annex/notes/design_principles/) established for IIIF
APIs. It is defined in terms of
[JSON-LD](https://www.w3.org/TR/json-ld/ "JSON-LD 1.0") and can be
seamlessly integrated with the existing IIIF APIs. The model can be used
to represent activities carried out by content publishers of creating,
updating, and deleting (or otherwise de-publishing) IIIF resources.

This section is a summary of the properties and types used by this
specification, and defined by Activity Streams. This is intended to ease
implementation efforts by collecting the relevant information together.

Properties, beyond those described in this specification, that the
consuming application does not have code to process *must* be ignored.
Other properties defined by Activity Streams *may* be used, such as
`origin` or `instrument`, but there are no current use cases that would
warrant their inclusion in this specification.

### 3.1. Ordered Collection <a href="#orderedcollection" class="anchorClass"></a>

The top-most resource for managing the lists of Activities is an Ordered
Collection, broken up into Ordered Collection Pages. The Collection does
not directly contain any of the Activities, instead it refers to the
`first` and `last` pages of the list.

The overall ordering of the Collection is from the oldest Activity as
the first entry in the first page, to the most recent as the last entry
in the last page. Consuming applications *should* therefore start at the
end and walk **backwards** through the list, and stop when they reach a
timestamp before the time they last processed the list.

Content providers *must* publish an Ordered Collection at the HTTP(S)
URI listed in the `id` property of the Collection.

##### id <a href="#id" class="anchorClass"></a>

The identifier of the Ordered Collection.

Ordered Collections *must* have an `id` property. The value *must* be a
string and it *must* be an HTTP(S) URI. The JSON representation of the
Ordered Collection *must* be available at the URI.

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{ "id": "https://example.org/activity/all-changes" }
```

</div>

</div>

##### type <a href="#type-ordered-collection" class="anchorClass"></a>

The class of the Ordered Collection.

Ordered Collections *must* have a `type` property. The value *must* be
`OrderedCollection`.

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{ "type": "OrderedCollection" }
```

</div>

</div>

##### first <a href="#first" class="anchorClass"></a>

A link to the first Ordered Collection Page for this Collection.

Ordered Collections *should* have a `first` property. The value *must*
be a JSON object, with the `id` and `type` properties. The value of the
`id` property *must* be a string, and it *must* be the HTTP(S) URI of
the first page of items in the Collection. The value of the `type`
property *must* be the string `OrderedCollectionPage`.

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "first": {
    "id": "https://example.org/activity/page-0",
    "type": "OrderedCollectionPage"
  }
}
```

</div>

</div>

##### last <a href="#last" class="anchorClass"></a>

A link to the last Ordered Collection Page for this Collection. As the
client processing algorithm works backwards from the most recent to
least recent, the inclusion of `last` is *required*, but `first` is only
*recommended*.

Ordered Collections *must* have a `last` property. The value *must* be a
JSON object, with the `id` and `type` properties. The value of the `id`
property *must* be a string, and it *must* be the HTTP(S) URI of the
last page of items in the Collection. The value of the `type` property
*must* be the string `OrderedCollectionPage`.

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "last": {
    "id": "https://example.org/activity/page-1234",
    "type": "OrderedCollectionPage"
  }
}
```

</div>

</div>

##### totalItems <a href="#totalitems" class="anchorClass"></a>

The total number of Activities in the entire Ordered Collection.

Ordered Collections *may* have a `totalItems` property. The value *must*
be a non-negative integer.

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{ "totalItems": 21456 }
```

</div>

</div>

##### seeAlso <a href="#seealso" class="anchorClass"></a>

This property is used to refer to one or more documents that
semantically describe **the set of resources** that are being acted upon
in the Activities within the Ordered Collection, rather than any
particular resource referenced from within the collection. This would
allow the Ordered Collection to refer to, for example, a
[DCAT](https://www.w3.org/TR/vocab-dcat/ "Data Catalog Vocabulary")
description of the dataset. For Ordered Collections that aggregate
activities and/or objects from multiple sources, the referenced
description should describe the complete aggregation rather than an
individual source.

Ordered Collections *may* have a `seeAlso` property. The value *must* be
an array of one or more JSON objects, with the `id` and `type`
properties. The value of the `id` property *must* be a string, and it
*must* be the HTTP(S) URI of the description of the dataset. The value
of the `type` property *must* be the string `Dataset`. Please note that
any resource that is intended to be used by software is tagged as
`Dataset`, including single files. The JSON object has the same
structure as in the Presentation API, and thus *should* have the
following properties:

- `format`, the value of which *must* be a string, and it *must* be the
  MIME media type of the referenced description document
- `label`, the value of which *must* be a JSON object, following the
  pattern for language maps described in the [Presentation
  API](/api/presentation/3.0/#language-of-property-values "Language of Property Values")
- `profile`, the value of which *must* be a string containing either a
  value from the [profiles registry](/api/registry/profiles/) or a URI

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "seeAlso": [
    {
      "id": "https://example.org/dataset/all-dcat.jsonld",
      "type": "Dataset",
      "label": { "en": [ "DCAT description of Collection" ] },
      "format": "application/ld+json",
      "profile": "http://www.w3.org/ns/dcat#"
    }
  ]
}
```

</div>

</div>

##### partOf <a href="#partof" class="anchorClass"></a>

This property is used to refer to a larger Ordered Collection, of which
this Ordered Collection is part. This would allow a publisher to have
thematic or temporal sets of activities, for example to have different
collections of activities for their paintings from their sculptures, or
their modern content from their archival content.

Ordered Collections *may* have a `partOf` property. The value *must* be
an array of one or more JSON objects, with the `id` and `type`
properties. The value of the `id` property *must* be a string, and it
*must* be the HTTP(S) URI of the larger collection. The value of the
`type` property *must* be the string `OrderedCollection`.

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "partOf": [
    {
      "id": "https://example.org/aggregated-changes",
      "type": "OrderedCollection"
    }
  ]
}
```

</div>

</div>

##### rights <a href="#rights" class="anchorClass"></a>

A string that identifies a license or rights statement that applies to
the usage of the Ordered Collection. The value *must* be drawn from the
set of [Creative
Commons](https://creativecommons.org/licenses/ "Create Commons Licenses")
license URIs, the
[RightsStatements.org](http://rightsstatements.org/page/1.0/ "rightsstatements.org")
rights statement URIs, or those added via the
[extension](/api/presentation/3.0/#46-linked-data-context-and-extensions "Linked Data Context and Extensions")
mechanism. The inclusion of this property is informative, and for
example could be used to display an icon representing the rights
assertions.

The value *must* be a string. If the value is drawn from Creative
Commons or RightsStatements.org, then the string *must* be a URI defined
by that specification.

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{ "rights": "http://creativecommons.org/licenses/by/4.0/" }
```

</div>

</div>

##### Complete Ordered Collection Example <a href="#complete-ordered-collection-example" class="anchorClass"></a>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "@context": "http://iiif.io/api/discovery/1/context.json",
  "id": "https://example.org/activity/all-changes",
  "type": "OrderedCollection",
  "totalItems": 21456,
  "rights": "http://creativecommons.org/licenses/by/4.0/",
  "seeAlso": [
    {
      "id": "https://example.org/dataset/all-dcat.jsonld",
      "type": "Dataset",
      "label": { "en": [ "DCAT description of Collection" ] },
      "format": "application/ld+json",
      "profile": "http://www.w3.org/ns/dcat#"
    }
  ],
  "partOf": [
    {
      "id": "https://example.org/aggregated-changes",
      "type": "OrderedCollection"
    }
  ],
  "first": {
    "id": "https://example.org/activity/page-0",
    "type": "OrderedCollectionPage"
  },
  "last": {
    "id": "https://example.org/activity/page-214",
    "type": "OrderedCollectionPage"
  }
}
```

</div>

</div>

### 3.2. Ordered Collection Page <a href="#ordered-collection-page" class="anchorClass"></a>

The list of Activities is ordered both from page to page by following
`prev` (or `next`) relationships, and internally within the page in the
`orderedItems` property. The number of entries in each page is up to the
implementer, and cannot be modified at request time by the client. Pages
are not required to have the same number of entries as any other page.

Content providers *must* publish at least one Ordered Collection Page at
the HTTP(S) URI given in the `id` property of the Page.

##### id <a href="#id-1" class="anchorClass"></a>

The identifier of the Collection Page.

Ordered Collection Pages *must* have an `id` property. The value *must*
be a string and it *must* be an HTTP(S) URI. The JSON representation of
the Ordered Collection Page *must* be available at the URI.

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{ "id": "https://example.org/activity/page-0" }
```

</div>

</div>

##### type <a href="#type-ordered-collection-page" class="anchorClass"></a>

The class of the Ordered Collection Page.

Ordered Collections *must* have a `type` property. The value *must* be
`OrderedCollectionPage`.

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{ "type": "OrderedCollectionPage" }
```

</div>

</div>

##### partOf <a href="#partof-1" class="anchorClass"></a>

The Ordered Collection of which this Page is a part.

Ordered Collection Pages *should* have a `partOf` property. The value
*must* be a JSON object, with the `id` and `type` properties. The value
of the `id` property *must* be a string, and *must* be the HTTP(S) URI
of the Ordered Collection that this page is part of. The value of the
`type` property *must* be the string `OrderedCollection`.

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "partOf": {
    "id": "https://example.org/activity/all-changes",
    "type": "OrderedCollection"
  }
}
```

</div>

</div>

##### startIndex <a href="#startindex" class="anchorClass"></a>

The position of the first item in this page’s `orderedItems` list,
relative to the overall ordering across all pages within the Collection.
The first entry in the overall list has a `startIndex` of 0. If the
first page has 20 entries, the first entry on the second page would
therefore be 20.

Ordered Collection Pages *may* have a `startIndex` property. The value
*must* be a non-negative integer.

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{ "startIndex": 20 }
```

</div>

</div>

##### next <a href="#next" class="anchorClass"></a>

A reference to the next page in the list of pages.

Ordered Collection Pages *should* have a `next` property, unless they
are the last page in the Collection. The value *must* be a JSON object,
with the `id` and `type` properties. The value of the `id` property
*must* be a string, and *must* be the HTTP(S) URI of the following
Ordered Collection Page. The value of the `type` property *must* be the
string `OrderedCollectionPage`.

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "next": {
    "id": "https://example.org/activity/page-2",
    "type": "OrderedCollectionPage"
  }
}
```

</div>

</div>

##### prev <a href="#prev" class="anchorClass"></a>

A reference to the previous page in the list of pages.

Ordered Collection Pages *must* have a `prev` property, unless they are
the first page in the Collection. The value *must* be a JSON object,
with the `id` and `type` properties. The value of the `id` property
*must* be a string, and *must* be the HTTP(S) URI of the preceding
Ordered Collection Page. The value of the `type` property *must* be the
string `OrderedCollectionPage`.

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "prev": {
    "id": "https://example.org/activity/page-1",
    "type": "OrderedCollectionPage"
  }
}
```

</div>

</div>

##### orderedItems <a href="#ordereditems" class="anchorClass"></a>

The Activities that are listed as part of this page. If the Activities
have an `endTime` property, then they *must* be ordered within the array
from the earliest datetime to the most recent datetime, in the same way
as the pages are ordered within the Ordered Collection.

Ordered Collection Pages *must* have an `orderedItems` property. The
value *must* be an array, with at least one item. Each item *must* be a
JSON object, conforming to the requirements of an Activity.

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "orderedItems": [
     {
        "type": "Update",
        "object": {
            "id": "https://example.org/iiif/1/manifest",
            "type": "Manifest"
        },
        "endTime": "2018-03-10T10:00:00Z"
     }
  ]
}
```

</div>

</div>

##### Complete Ordered Collection Page Example <a href="#complete-ordered-collection-page-example"
class="anchorClass"></a>

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "@context": "http://iiif.io/api/discovery/1/context.json",
  "id": "https://example.org/activity/page-1",
  "type": "OrderedCollectionPage",
  "startIndex": 20,
  "partOf": {
    "id": "https://example.org/activity/all-changes",
    "type": "OrderedCollection"
  },
  "prev": {
    "id": "https://example.org/activity/page-0",
    "type": "OrderedCollectionPage"
  },
  "next": {
    "id": "https://example.org/activity/page-2",
    "type": "OrderedCollectionPage"
  },
  "orderedItems": [
    {
      "type": "Update",
      "object": {
        "id": "https://example.org/iiif/1/manifest",
        "type": "Manifest"
      },
      "endTime": "2018-03-10T10:00:00Z"
    }
  ]
}
```

</div>

</div>

### 3.3. Activities <a href="#activities" class="anchorClass"></a>

The Activities are the means of describing the changes that have
occurred in the content provider’s system.

Content providers *may* publish Activities separately from Ordered
Collection Pages, and if so they *must* be at the HTTP(S) URI given in
the `id` property of the Activity.

##### id <a href="#id-2" class="anchorClass"></a>

An identifier for the Activity.

Activities *may* have an `id` property. The value *must* be a string and
it *must* be an HTTP(S) URI. The JSON representation of the Activity
*may* be available at the URI.

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{ "id": "https://example.org/activity/1" }
```

</div>

</div>

##### type <a href="#type-activity" class="anchorClass"></a>

The type of Activity.

This specification uses the types described in the table below.

| Type | Definition |
|----|----|
| `Create` | The initial creation of the resource. Each resource *should* have at most one `Create` Activity in which it is the `object`, but if the URI of the resource is re-used after a `Delete` activity, then there *may* be more than one. |
| `Update` | Any change to the resource. In a system that does not distinguish creation from modification, then all changes *may* have the `Update` type. |
| `Delete` | The deletion of the resource, or its de-publication from the web. Each resource *should* have at most one `Delete` Activity in which it is the `object`, but *may* have more than one if it is subsequently republished and then deleted again. |
| `Move` | The re-publishing of the resource at a new URI, with the same content. Each resource *may* have zero or more `Move` activities in which it is the `object` or `target`. |
| `Add` | The addition of an object to a stream, outside of any of the above types of activity, such as a third party aggregator adding resources from a newly discovered stream. Each resource *should* have at most one `Add` Activity in which it is the object, but if the resource is re-added after a `Remove` activity, then there *may* be more than one. The `Add` Activity *should not* be present if a `Create` or `Update` Activity is present at the same time. |
| `Remove` | The removal of an object from a stream, outside of any of the above types of activity, such as a third party aggregator removing resources from a stream that are no longer considered to be in scope. Each resource *should* have at most one `Remove` activity, but if the resource is re-added and then re-removed, then there *may* be more than one. The `Remove` Activity *should not* be present if a `Delete` Activity is present at the same time. |
| `Refresh` | The beginning of an activity to refresh the stream with the state of all of the resources. It does not have an `object` or `target`. |

Activities *must* have the `type` property. The value *must* be a
registered Activity type, and *should* be one of `Create`, `Update`, or
`Delete`.

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{ "type": "Update" }
```

</div>

</div>

##### object <a href="#object" class="anchorClass"></a>

The IIIF resource that was affected by the Activity. It is an
implementation decision whether there are separate lists of Activities,
one per object type, or a single list with all of the object types
combined.

In the case of the `Move` activity, the `object` property contains the
`id` and `type` of the source from whence it was moved. The new location
will be in the `target` property, described below.

Activities *must* have the `object` property. The value *must* be a JSON
object, with the `id` and `type` properties. The `id` *must* be an
HTTP(S) URI. The `type` *should* be a class defined in the IIIF
Presentation API, and *should* be one of `Collection`, or `Manifest`.
The `type`, therefore, *may* be any class, including those not defined
by the IIIF Presentation API, and consuming applications *should*
validate the `type` as being one that is appropriate for their usage.

The object *may* have a `seeAlso` property, as defined for
`OrderedCollection` above, to reference a document that describes the
object resource. The document referenced in the `seeAlso` property *may*
also be referenced with the `seeAlso` property in an instance of the
IIIF Presentation API. The `type` of the document referenced in the
`seeAlso` property should be given as `Dataset`, meaning that it is data
rather than a human-readable document.

The object *may* have a `canonical` property, the value of which *must*
be a string that contains a URI. This URI identifies the resource,
regardless of the URI given in the `id` property of the object, which
might be specific to a format, API version or publishing platform. The
use of this property allows changes to be aligned across representations
without relying on `seeAlso` links or only having a single
representation.

The object *may* have a `provider` property, as defined by the [IIIF
Presentation API](https://iiif.io/api/presentation/3.0/#provider). In
particular, the value of the property *must* be an array of JSON
objects, each of which *must* have the `id`, `type` and `label`
attributes, carrying the URI of the provider, the string “Agent”, and
the name of the provider in a language map object, respectively.

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "object": {
    "id": "http://example.org/iiif/v3/1/manifest",
    "type": "Manifest",
    "canonical": "https://example.org/iiif/1",
    "seeAlso": [
      {
        "id": "https://example.org/dataset/single-item.jsonld",
        "type": "Dataset",
        "label": { "en": [ "Object Description in Schema.Org" ] },
        "format": "application/ld+json",
        "profile": "https://schema.org/"
      }
    ],
    "provider": [
      {
        "id": "https://example.org/about",
        "type": "Agent",
        "label": { "en": [ "Example Organization" ] }
      }
    ]
  }
}
```

</div>

</div>

##### target <a href="#target" class="anchorClass"></a>

The new location of the IIIF resource, after it was affected by a `Move`
activity.

`Move` activities *must* have the `target` property. The value *must* be
a JSON object, with the `id` and `type` properties. The `id` *must* be
an HTTP(S) URI, and *must* be different from the URI given in the
`object` property’s `id`. The `type` *should* be a class defined in the
IIIF Presentation API, and *should* be the same as the `object`
property’s `type`. Other properties that are usable for the description
of `object`, such as `seeAlso` and `canonical` are also available for
use in describing the `target`.

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "target": {
    "id": "http://example.org/a/manifest",
    "type": "Manifest",
    "seeAlso": [
      {
        "id": "https://example.org/single-item-a.jsonld",
        "type": "Dataset",
        "format": "application/ld+json"
      }
    ]
  }
}
```

</div>

</div>

##### endTime <a href="#endtime" class="anchorClass"></a>

The time at which the Activity was finished. It is up to the implementer
to decide whether the value of `endTime` is the timestamp for the
publication of the IIIF resource online or is the timestamp of the
modification to the data in the managing system if these are different,
but the decision *must* be consistently applied. The changed resource
given in `object` *must* be available at its URI at or before the
timestamp given in `endTime`. The value of `endTime` *should* be before
the time that the Activity is published as part of its Ordered
Collection.

Activities *should* have the `endTime` property. The value *must* be a
datetime expressed in UTC in the
[xsd:dateTime](https://www.w3.org/TR/xmlschema11-2/#dateTime "XSD DateTime")
format.

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{ "endTime": "2017-09-21T00:00:00Z" }
```

</div>

</div>

##### startTime <a href="#starttime" class="anchorClass"></a>

The time at which the Activity was started.

Activities *may* have the `startTime` property. The value *must* be a
datetime expressed in UTC in the
[xsd:dateTime](https://www.w3.org/TR/xmlschema11-2/#dateTime "XSD DateTime")
format.

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{ "startTime": "2017-09-20T23:58:00Z" }
```

</div>

</div>

##### summary <a href="#summary" class="anchorClass"></a>

A short textual description of the Activity. This is intended primarily
to be used for debugging purposes or explanatory messages, and thus does
not have the requirement for internationalization of the content. The
intended audience of this field is a human who manages an aggregation
service and is looking at the data, not an end user of the IIIF
resource. It is not recommended that this field be present as in most
situations it will never be seen.

Activities *may* have the `summary` property. The value *must* be a
string.

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{ "summary": "admin updated the manifest, fixing reported bug #15." }
```

</div>

</div>

##### actor <a href="#actor" class="anchorClass"></a>

The organization, person, or software agent that carried out the
Activity.

Activities *may* have the `actor` property. The value *must* be a JSON
object, with the `id` and `type` properties. The `id` *should* be an
HTTP(S) URI. The `type` *must* be one of `Application`, `Organization`,
or `Person`.

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "actor": {
    "id": "https://example.org/person/admin1",
    "type": "Person"
  }
}
```

</div>

</div>

##### Complete Activity Example <a href="#complete-activity-example" class="anchorClass"></a>

A complete example Activity would thus look like the following example.
Note that it does not have a `@context` property, as it is always
embedded within a `CollectionPage`. Please note also that this is a
complete example with all possible fields; most implementations will not
need nor expose this level of data.

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "@context": "http://iiif.io/api/discovery/1/context.json",
  "id": "https://example.org/activity/1",
  "type": "Update",
  "summary": "admin updated the manifest, fixing reported bug #15.",
  "object": {
    "id": "https://example.org/iiif/1/manifest",
    "type": "Manifest",
    "canonical": "https://example.org/iiif/1",
    "seeAlso": [
      {
        "id": "https://example.org/dataset/single-item.jsonld",
        "type": "Dataset",
        "format": "application/ld+json"
      }
    ]
  },
  "endTime": "2017-09-21T00:00:00Z",
  "startTime": "2017-09-20T23:58:00Z",
  "actor": {
    "id": "https://example.org/person/admin1",
    "type": "Person"
  }
}
```

</div>

</div>

### 3.4. Linked Data Context and Extensions <a href="#34-linked-data-context-and-extensions"
class="anchorClass"></a>

#### 3.4.1. @context <a href="#341-context" class="anchorClass"></a>

The top level resource in the response *must* have the `@context`
property, and it *should* appear as the very first key/value pair of the
JSON representation. This property lets Linked Data processors interpret
the document as a graph. The value of the property *must* be either the
URI of the IIIF Discovery context document,
`http://iiif.io/api/discovery/1/context.json`, or an array of strings,
where the URI of the IIIF Discovery context document is the last item in
the array.

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "@context": "http://iiif.io/api/discovery/1/context.json"
}
```

</div>

</div>

#### 3.4.2. Extensions <a href="#342-extensions" class="anchorClass"></a>

If any additional types or properties are desired beyond the ones
defined in this specification or the ActivityStreams specification, then
those types or properties *should* be mapped to RDF terms in one or more
additional context documents. These extension contexts *should* be added
to the top level `@context` property, and *must* be before the URI of
the Discovery context. The JSON-LD 1.1 functionality of defining terms
only within a specific property, known as [scoped
contexts](https://json-ld.org/spec/latest/json-ld/#scoped-contexts "JSON-LD Scoped Contexts"),
*must* be used to minimize cross-extension collisions. Extensions
intended for broad use *should* be registered in the [extensions
registry](/api/registry/ "IIIF Extension Registry").

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "@context": [
    "http://example.org/extension/context.json",
    "http://iiif.io/api/discovery/1/context.json"
  ]
}
```

</div>

</div>

### 3.5. Activity Streams Processing Algorithm <a href="#activity-streams-processing-algorithm"
class="anchorClass"></a>

The aim of the processing algorithm is to inform developers implementing
consuming applications how to make best use of the available
information. The specification does not require any particular
processing of the information by the consuming application, but
considers indexing of the resource as a common use case in [section
3.5.3](#indexing).

Any other algorithm that arrives at the same results as an
implementation of the algorithms specified below would also be
considered to be conforming. The algorithms are provided as
recommendations (*should*) rather than strict requirements in order to
not overly constrain the usage or inhibit novel ideas and
experimentation.

For processing multiple streams concurrently, there is additional
processing work to be done to ensure the correct results, as the same
activity might be represented in multiple streams. This is described in
[section 3.5.4](#processing-multiple).

#### 3.5.1. Collection Algorithm <a href="#collection-algorithm" class="anchorClass"></a>

Given the URI of an ActivityStreams Collection (`collection`) as input,
a conforming processor *should*:

1.  Initialization:
    1.  Let `processedItems` be an empty array
    2.  Let `lastCrawl` be the timestamp of the previous time the
        algorithm was executed or null if this is the first time the
        stream has been processed
    3.  Let `onlyDelete` be `False`
2.  Retrieve the representation of `collection` via HTTP(S)
3.  Validate that the retrieved representation contains at least the
    features required for processing
4.  Find the URI of the last page at `collection.last.id` (`pageN`)
5.  Apply the results of the page algorithm to `pageN`

#### 3.5.2. Page Algorithm <a href="#page-algorithm" class="anchorClass"></a>

Given the URI of an ActivityStreams CollectionPage (`page`), a list of
processed items (`processedItems`), the date of last crawling
(`lastCrawl`), and a processing function (`process()`) as input, a
conforming processor *should*:

1.  Retrieve the representation of `page` via HTTP(S)
2.  Validate that the retrieved representation contains at least the
    features required for processing
3.  Find the set of updates of the page at `page.orderedItems` (`items`)
4.  In **reverse order**, iterate through the activities (`activity`) in
    `items`:
    1.  If `activity.endTime` is before `lastCrawl`, then terminate ;
    2.  If `activity.type` is `Refresh`, then if `lastCrawl` is not
        null, then set `onlyDelete` to `True`, else if `lastCrawl` is
        null, then terminate;
    3.  If the updated resource's URI at `activity.object.id` is in
        `processedItems`, then continue ;
    4.  If the updated resource's class at `activity.object.type` is not
        one that is known to the processor, then continue ;
    5.  Otherwise, if `activity.type` is `Delete`, or it is `Remove` and
        `activity.origin.id` is the URI of the current stream, then find
        the URI of the resource at `activity.object.id` and process its
        removal ;
    6.  Otherwise, if `onlyDelete` is `True`, then continue ;
    7.  Otherwise, if `activity.type` is `Update` or `Create`, or it is
        `Add` and `activity.target.id` is the URI of the current stream,
        then find the URI of the resource at `activity.object.id`
        (`object`) and process its inclusion ;
    8.  Otherwise, if `activity.type` is `Move`, then find the original
        URI of the moved resource at `activity.object` and process its
        removal, and find the new URI of the moved resource at
        `activity.target` and process its inclusion.
    9.  Add the processed resource's URI to `processedItems`
5.  Finally, find the URI of the previous page at `collection.prev.id`
    (`pageN1`)
6.  If there is a previous page, apply the results of the page algorithm
    to `pageN1`

#### 3.5.3. Resource Processing: Indexing <a href="#indexing" class="anchorClass"></a>

While there are many possible algorithms to process the discovered
resources and activities, a core use case for the Change Discovery API
is to maintain an up-to-date index of the resources.

In this case, the objective of the consuming application is to find
accurate, machine-readable descriptive information that might be used to
build an index, and thus the application *should* use the IIIF
Presentation API `seeAlso` property to retrieve such a description if
available. For different types of resources, and for different domains,
the referenced descriptive resources will have different formats and
semantics. If there are no such descriptions, or none that can be
processed, the data in the Manifest and in other IIIF resources might be
used as a last resort, despite its presentational intent.

#### 3.5.4. Processing Multiple Streams <a href="#processing-multiple" class="anchorClass"></a>

In order to process multiple streams simultaneously, the steps for
processing a page should be followed, but applied to the set of changes
across all of the streams, sorted by the timestamp of the activity. One
motivating factor for this is that the same activity might appear in
multiple streams, when the activities have been broadly aggregated. For
example, the same update might occur in three streams out of ten that
are being processed together, and should only be processed once.

Implementations that process activities beyond the most recent per
resource should consider two activities with the same `type`,
`object.id` and `endTime` to be the same activity regardless of any
other properties. In this way, duplicate activities can be detected even
if different streams maintain different degrees of description and
information, or some implementations have activities available at their
URIs and some do not.

The algorithm below does not take into account any optimizations or
constraints around memory or processing. A more sophisticated algorithm
might process pages, relying on each being sorted, to keep an
interleaved buffer of activities full, rather than retrieving and
processing everything before starting to process the activities. It is
not described in as much detail as the processing algorithms above for
this reason.

Given an array (`collections`) of collection URIs as input,

1.  Initialize global values `processedItems` and `lastCrawl` as above.
2.  Let `allActivities` be an empty array.
3.  For each `collection` in `collections`:
    1.  Retrieve and validate the representation of `collection`.
    2.  While there are pages with activities that have a timestamp
        after `lastCrawl`:
        1.  Retrieve and validate the representation of the page, and
            add the matching activities to `allActivities`
4.  Sort `allActivities` by `activity.endTime`, descending, removing any
    duplicates as described above.
5.  For each activity in `allActivities`, apply the page algorithm's
    handling of an activity.

## 4. Network Considerations <a href="#4-network-considerations" class="anchorClass"></a>

### 4.1. Media Type <a href="#41-media-type" class="anchorClass"></a>

The base format for all responses of this API is JSON, as described
above.

If the server receives a request with an `Accept` header, it *should*
respond following the rules of [content
negotiation](https://tools.ietf.org/html/rfc7231#section-5.3.2 "HTTP 1.1, 5.3.2. Accept").
Note that content types provided in the `Accept` header of the request
*may* include parameters, for example `profile` or `charset`.

If the request does not include an `Accept` header, the HTTP
`Content-Type` header of the response *should* have the value
`application/ld+json` (JSON-LD) with the `profile` parameter given as
the context document: `http://iiif.io/api/discovery/1/context.json`.

``` urltemplate
Content-Type: application/ld+json;profile="http://iiif.io/api/discovery/1/context.json"
```

If the above `Content-Type` header value cannot be generated, then the
value *should* instead be `application/json` (regular JSON), without a
`profile` parameter.

``` urltemplate
Content-Type: application/json
```

The HTTP server *should* follow the [CORS
requirements](https://www.w3.org/TR/cors/ "Cross-Origin Resource Sharing")
to enable browser-based clients to retrieve the responses. Recipes for
enabling CORS and conditional Content-Type headers are provided in the
[Apache HTTP Server Implementation
Notes](/api/annex/notes/apache/ "Apache HTTP Server Implementation Notes").
Responses *should* be compressed by the server as there are significant
performance gains to be made for very repetitive data structures.

### 4.2. Activities for Access-Restricted Content <a href="#42-activities-for-access-restricted-content"
class="anchorClass"></a>

Activities *may* be published about content that has access
restrictions. Clients *must not* assume that they will be able to access
every resource that is the object of an Activity, and *must not* assume
that it has been deleted if it is inaccessible. For example, the content
might be protected by an authentication system that is denying access
(an end user might be able to provide the right credentials to gain
access) or there may be a temporary network outage preventing the
content from being retrieved (the network will eventually be restored).

Content may also change from being available to being protected by
access restrictions, or become available having previously been
protected. There are no more specific activity types for these
situations, and the publisher *should* issue the regular `Update` or
`Delete` activities accordingly.

### 4.3. Negotiable Resources <a href="#43-negotiable-resources" class="anchorClass"></a>

Some HTTP(S) URIs are able to respond with different representations of
the same content in response to requests with different headers, such as
the same URI being able to return both version 2 and version 3 of the
IIIF Presentation API based on the Accept header. This is known as
“content negotiation”, and such resources are known as “negotiable
resources”. The representations that can be negotiated for are known as
“variants”.

Negotiable resources are not supported by the Discovery API, only
variants. This means that there would be one Activity entry for each of
the representations that are available, and that each representation
*must* have its own URI, even if it can also be reached via the
negotiable resource. In the case of negotiating for different versions
of the IIIF Presentation API, the `format` property can be used to
include the full media type of the resource, where the version-specific
context document is given in the `profile` parameter. If there are
additional descriptive resources available, each such resource would
describe all of the variants, and thus the `seeAlso` property of each
Activity would refer to the same descriptions, allowing the variants to
be connected together.

Two variants of the same negotiable resource can be represented as
follows.

<div class="language-json-doc highlighter-rouge">

<div class="highlight">

``` highlight
{
  "orderedItems": [
    {
      "type": "Update",
      "object": {
        "id": "https://example.org/iiif/1/manifest/v2",
        "type": "Manifest",
        "seeAlso": "https://example.org/iiif/1/metadata.xml",
        "format": "application/ld+json;profile=\"https://iiif.io/api/presentation/2/context.json\""
      },
      "endTime": "2018-03-10T10:00:00Z"
    },
    {
      "type": "Update",
      "object": {
        "id": "https://example.org/iiif/1/manifest/v3",
        "type": "Manifest",
        "seeAlso": "https://example.org/iiif/1/metadata.xml",
        "format": "application/ld+json;profile=\"https://iiif.io/api/presentation/3/context.json\""
      },
      "endTime": "2018-03-10T10:00:00Z"
    }
  ]
}
```

</div>

</div>

## Appendices <a href="#appendices" class="anchorClass"></a>

### A. Acknowledgements <a href="#acknowledgements" class="anchorClass"></a>

Many thanks to the members of the [IIIF
community](https://iiif.io/community/ "IIIF Community") for their
continuous engagement, innovative ideas, and feedback.

This specification is due primarily to the work of the [IIIF Discovery
Technical Specification
Group](https://iiif.io/community/groups/discovery/), chaired by Antoine
Isaac (Europeana), Matthew McGrattan (Digirati) and Robert Sanderson
(Yale University). The IIIF Community thanks them for their leadership,
and the members of the group for their tireless work.

### B. Change Log <a href="#change-log" class="anchorClass"></a>

| Date       | Description                    |
|------------|--------------------------------|
| 2021-06-22 | Version 1.0 (Zooming Heatwave) |
| 2021-04-28 | Version 0.9.2 (unnamed)        |
| 2020-09-29 | Version 0.9.1 (unnamed)        |
| 2020-06-04 | Version 0.9 (unnamed)          |
| 2019-11-01 | Version 0.4 (unnamed)          |
| 2019-03-20 | Version 0.3 (unnamed)          |
| 2018-11-12 | Version 0.2 (unnamed)          |
| 2018-05-04 | Version 0.1 (unnamed)          |

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
