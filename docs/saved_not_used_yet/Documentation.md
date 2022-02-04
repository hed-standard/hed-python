# Documentation


## 1. HED publications

Explanation of the history, development, and motivation for third generation HED: 

> Robbins, K., Truong, D., Jones, A., Callanan, I., & Makeig, S. (2020, August 1).
> Building FAIR functionality: Annotating events in time series data using Hierarchical Event Descriptors (HED).
> [https://doi.org/10.31219/osf.io/5fg73](https://doi.org/10.31219/osf.io/5fg73)

Detailed case study in using HED-3G for tagging:

> Robbins, K., Truong, D., Appelhoff, S., Delorme, A., & Makeig, S. (2021, May 7). 
> Capturing the nature of events and event context using Hierarchical Event Descriptors (HED). 
> BioRxiv, 2021.05.06.442841. 
> [https://doi.org/10.1101/2021.05.06.442841](https://doi.org/10.1101/2021.05.06.442841)

## 2. Working documents

Mapping of HED terms and their descriptions to known ontologies is:

> HED-3G Working Document on Ontology mapping
> [https://drive.google.com/file/d/13y17OwwNBlHdhB7hguSmOBdxn0Uk4hsI/view?usp=sharing](https://drive.google.com/file/d/13y17OwwNBlHdhB7hguSmOBdxn0Uk4hsI/view?usp=sharing)

Two other working documents hold portions of the HED-3G specification that are under development 
and will not be finalized for Release 1:

> HED-3G Working Document on Spatial Annotation
> [https://docs.google.com/document/d/1jpSASpWQwOKtan15iQeiYHVewvEeefcBUn1xipNH5-8/view?usp=sharing](https://docs.google.com/document/d/1jpSASpWQwOKtan15iQeiYHVewvEeefcBUn1xipNH5-8/view?usp=sharing)

> HED-3G Working Document on Task Annotation
> [https://docs.google.com/document/d/1eGRI_gkYutmwmAl524ezwkX7VwikrLTQa9t8PocQMlU/view?usp=sharing](https://docs.google.com/document/d/1eGRI_gkYutmwmAl524ezwkX7VwikrLTQa9t8PocQMlU/view?usp=sharing)

## 3. Schema viewers

The HED schema is usually developed in `.mediawiki` format and converted to XML for use by tools.
However, researchers wishing to tag datasets will find both of these views hard to read. 
For this reason, we provide links to three versions of the schema. The expandable
HTML viewer is easier to navigate. Annotators can also use CTAGGER, which includes a schema viewer
and tagging hints.

`````{list-table} HED web-based schema vocabulary viewers.
:header-rows: 1
:widths: 20 50

* - Viewer
  - Link
* - Expandable HTML	
  - [https://www.hedtags.org/display_hed.html?version=8.0.0](https://www.hedtags.org/display_hed.html?version=8.0.0)
* - Mediawiki	
  - [https://github.com/hed-standard/hed-specification/blob/master/hedwiki/HED8.0.0.mediawiki](https://github.com/hed-standard/hed-specification/blob/master/hedwiki/HED8.0.0.mediawiki)
* - XML	
  - [https://github.com/hed-standard/hed-specification/blob/master/hedxml/HED8.0.0.xml](https://github.com/hed-standard/hed-specification/blob/master/hedxml/HED8.0.0.xml)
`````  

## 4. HED Websites

The following is a summary of the HED-related websites


`````{list-table} HED websites.
:header-rows: 1
:widths: 20 50

* - Description
  - Site
* - **Information and documentation**
  -
* - HED organization website	
  - [https://www.hedtags.org](https://www.hedtags.org)
* - HED organization github	
  - [https://github.com/hed-standard](https://github.com/hed-standard)
* - HED specification repository	
  - [https://github.com/hed-standard/hed-specification](https://github.com/hed-standard/hed-specification)
* - Examples of HED annotation
  - [https://github.com/hed-standard/hed-examples](https://github.com/hed-standard/hed-examples)
* - HED documentation website
  - [https://github.com/hed-standard/hed-standard.github.io](https://github.com/hed-standard/hed-standard.github.io)  
* - **HED Python resources**
  - 
* - Python code repository	
  - [https://github.com/hed-standard/hed-python](https://github.com/hed-standard/hed-python)
* - Python validator and tools	
  - [https://github.com/hed-standard/hed-python/tree/master/hedtools](https://github.com/hed-standard/hed-python/tree/master/hedtools)
* - **HED JavaScript resources**
  -
* - HED JavaScript code	
  - [https://github.com/hed-standard/hed-javascript](https://github.com/hed-standard/hed-javascript)
* - BIDS validator	
  - [https://github.com/bids-standard/bids-validator](https://github.com/bids-standard/bids-validator)
* - **HED Matlab resources**
  -
* - Matlab source code	
  - [https://github.com/hed-standard/hed-matlab](https://github.com/hed-standard/hed-matlab)
* - **Annotator resources**
  -
* - CTAGGER executable jar	
  - [https://github.com/hed-standard/hed-java/raw/master/ctagger.jar](https://github.com/hed-standard/hed-java/raw/master/ctagger.jar)
* - CTAGGER repository	
  - [https://github.com/hed-standard/CTagger](https://github.com/hed-standard/CTagger)
* - Java repository	
  - [https://github.com/hed-standard/hed-java](https://github.com/hed-standard/hed-java)
* - **Online HED tools**
  -
* - Online website	
  - [https://hedtools.ucsd.edu/hed](https://hedtools.ucsd.edu/hed)
* - Docker deployment	
  - [https://github.com/hed-standard/hed-python/tree/master/webtools/deploy_hed](https://github.com/hed-standard/hed-python/tree/master/webtools/deploy_hed)
`````