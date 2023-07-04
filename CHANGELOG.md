Release 0.3.1 July 3, 2023
- Pinned the version of the pydantic and inflect libraries due to inflict.
- Reorganized JSON output of remodeling summaries so that all of consistent form.
- Fixed summarize_hed_tags_op so that tags were correctly categorized for output.
- Minor refactoring to reduce code complexity.
- BaseInput and Sidecar now raise HedFileError if input could not be read.


Release 0.3.0 June 20, 2023
- Introduction of partnered schema.
- Improved error handling for schema validation.
- Support of Inset tags.
- Support of curly brace notation in sidecars.
- Expanded remodeling functionality.
- Refactoring of models to rely on DataFrames.
- Expanded unit tests in conjunction with specification tests.

Release 0.2.0 February 14, 2023
- First release of the HED remodeling tools.
- Reorganization of branches to reflect stages of development.
- Updating of schema cache with local copies.
- Improved schema validation and error messages.
- First pass at search and summarization.

Release 0.1.0  June 20, 2022
- First release on PyPI