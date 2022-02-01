# 2. HED terminology

The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT",
"RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in
[[RFC2119](https://www.ietf.org/rfc/rfc2119.txt)].

This specification uses a list of terms and abbreviations whose meaning is clarified here. 
Note: We here hyphenate multi-word terms as they appear in HED strings themselves; in plain text 
usage they may not need to be hyphenated. Starred variables [*] correspond to actual HED tags.  


## Agent [*]

A person or thing, living or virtual, that produces (or appears to participants to be ready and
capable of producing) specified effects. Agents include the study participants from whom data is
collected. Virtual agents may be human or other actors in virtual-reality or augmented-reality
paradigms or on-screen in video or cartoon presentations (e.g., an actor interacting with the
recorded participant in a social neuroscience experiment, or a dog or robot active in a live 
action or animated video).

## Condition-variable [*]

An aspect of the experiment that is set or manipulated during the experiment to observe an effect
or to manage bias. Condition variables are sometimes called independent variables.

## Control-variable [*]

An aspect of the experiment that is fixed throughout the study and usually is explicitly 
controlled.

## Dataset

A set of neuroimaging and behavioral data acquired for a purpose of a particular study. 
A dataset consists of data recordings acquired from one or more subjects, possibly from 
multiple sessions and sensor modalities. A dataset is often referred to as a study.

## Event [*]

Something that happens during the recording or that may be perceived by a participant 
as happening, to which a time of occurrence (most typically onset or offset) can be 
identified. Something expected by a participant to happen at a certain time that 
does not happen can also be a meaningful recording event. The nature of other events
may be known only to the experimenter or to the experiment control application 
(e.g., undisclosed condition changes in task parameters).

## Event-context [*]

Circumstances forming or contributing to the setting in which an event occurs that 
are relevant to its interpretation, assessment, and consequences.

## Event-stream [*]

A named sequence of events such as all the events that are face stimuli or all of 
the events that are participant responses.

## Experiment-participant [*]

A living agent, particularly a human from whom data is acquired during an experiment,
though in some paradigms other human participants may also play roles.

## Experimental-trial [*]
A contiguous data period that is considered a unit used to observe or measure something,
typically a data period including an expected event sequence that is repeated many times
during the experiment (possibly with variations). Example: a repeating sequence of stimulus
presentation, participant response action, and sensory feedback delivery events in a 
sensory judgment task.

## HED schema [*]
A formal specification of the vocabulary and rules of a particular version of HED for 
use in annotation, validation, and analysis. A HED schema is given in XML (`.xml`) format. 
The top-level versioned HED schema is used for all HED event annotations. Named and 
versioned HED library schema may be used as well to make use of descriptive terms used 
by a particular research community. (For example, an experiment on comprehension of 
connected speech might annotate events using a grammatical vocabulary contained in a 
linguistics HED schema library.)

## HED string

A comma-separated list of HED tags and/or tag-groups. 

## HED tag

A valid path along one branch of a HED vocabulary hierarchy. A valid long-form HED tag 
is a slash-separated path following the schema tree hierarchy from its root to a term 
along some branch. Any suffix of a valid long-form HED tag is a valid short-form HED tag. 
No white space is allowed within terms themselves. For example, the long form of the 
HED tag specifying an experiment participant is: *Property/Agent-property/Agent-task-role/Experiment-participant*.
Valid short-form tags are *Experiment-participant*, *Agent-task-role/Experiment-participant*, 
and *Agent-property/Agent-task-role/Experiment-participant*. HED tools should treat 
long-form and short-form tags interchangeably.

## Indicator-variable [*]

An aspect of the experiment or task that is measured or calculated for analysis. 
Indicator variables, sometimes called dependent variables, can be data features 
that are calculated from measurements rather than aspects that are directly measured. 

## Parameter [*]

An experiment-specific item, often a specific behavioral or computer measure, that 
is useful in documenting the analysis or assisting downstream analysis.

## Recording [*]

A continuous recording of data from an instrument in a single session without 
repositioning the recording sensors.

## Tag-group

One or more valid, comma-separated HED tags or enclosed in parentheses to indicate 
that these tags belong together. Tag-groups may contain arbitrary nestings of other 
tags and tag-groups.

## Task [*] 

A set of structured activities performed by the participant that are integrally 
related to the purpose of the experiment. Tasks often include observations and responses to
sensory presentations as well as specified actions in response to presented situations.

## Temporal scope

The time interval between events marking the beginning and end of something in the 
experiment. The time between and including the onset and offset of an event.

## Time-block [*]

A contiguous portion of the data recording during which some aspect of the experiment 
is fixed or noted.
