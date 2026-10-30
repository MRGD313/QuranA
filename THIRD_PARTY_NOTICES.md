# Third-Party Notices — QuranA

QuranA (قرآنا) uses two external datasets. Neither dataset is committed to this
repository. `scripts/download_data.py` fetches them from their official sources.
This file records provenance, versions, and terms. It is not legal advice.

## 1. Quran text — Tanzil Project

- **Work:** Tanzil Quran Text (Uthmani), version 1.1 (February 2021)
- **Source:** https://tanzil.net/download/
- **Copyright:** © Tanzil Project (tanzil.net)
- **Terms of use (https://tanzil.net/docs/Text_License):**
  - Permission is granted to copy and distribute verbatim copies of the Quran
    text, but changing the text is not allowed.
  - The text can be used in any website or application provided its source
    (Tanzil Project) is clearly indicated and a link is made to
    https://tanzil.net/ so users can track changes.
- **How QuranA complies:** the text is stored unchanged; every report generated
  by QuranA names Tanzil and the exact version; this file links to tanzil.net.
  The text is downloaded at setup time and is excluded from the Git repository.

## 2. Morphological annotation — Quranic Arabic Corpus

- **Work:** Quranic Arabic Corpus, morphology version 0.4
- **Source:** https://corpus.quran.com/download
- **Author:** Kais Dukes, Language Research Group, University of Leeds
- **License:** GNU General Public License (see https://corpus.quran.com/license.jsp)
- **Terms include:**
  - Permission is granted to copy and distribute verbatim copies, but changing
    the annotation is not allowed.
  - The annotation may be used in any website or application provided its source
    (the Quranic Arabic Corpus) is clearly indicated and a link is made to
    https://corpus.quran.com/.
  - The copyright notice must be reproduced in copies and derived works.
- **How QuranA complies:** the file is downloaded unchanged; the copyright
  notice is preserved inside it; QuranA names the corpus and its version in
  every report and in this file. `data/quran.db` is a derived local index built
  from this annotation and is not distributed in the repository.

## 3. Surah metadata — Tanzil Project

- **Work:** Quran metadata (quran-data.xml), version 1.0
- **Source:** http://tanzil.net/res/text/metadata/quran-data.xml
- **License:** Creative Commons Attribution (cc-by)
- **Use:** surah names and verse counts used for validation.

## Runtime dependency: Bale Bot API

QuranA talks to the Bale messenger Bot API (`https://tapi.bale.ai`). Bale is an
independent service; use of the API is subject to Bale's own terms.
