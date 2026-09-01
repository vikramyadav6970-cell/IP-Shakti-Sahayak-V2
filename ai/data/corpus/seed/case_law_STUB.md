# case_law_STUB.md

Intentionally empty of records.

I searched for a real, verifiable Indian (or foreign) **court** judgment squarely
addressing Section 3(p) or Ayurveda-related traditional-knowledge patentability,
to seed this collection the same way `ipr_prior_art.jsonl` was seeded. I did not
find one I could confirm with enough confidence to include here.

What exists and *is* seeded (in `ipr_prior_art.jsonl`) are patent-office
administrative/opposition proceedings — the turmeric (USPTO reexamination), neem
(EPO Opposition Division + Technical Board of Appeal), and Basmati (USPTO
reexamination) matters. These are **not court judgments** — they belong in
`ipr_prior_art`, per the schema's own distinction (`case_law`'s schema explicitly
expects a `court` field like "Supreme Court of India").

**Do not fabricate a case here to fill the gap.** A fictional court judgment with
an invented case name, court, and holding is exactly the failure mode this
project's guardrails exist to prevent, and it is more dangerous in `case_law`
than almost anywhere else in the corpus — a user could reasonably rely on "the
Supreme Court held X" in a way they might not rely on a paraphrased statute
summary.

**Next step for whoever picks up T1.1 or a dedicated case-law task:** search
Indian Kanoon (indiankanoon.org) or SCC Online for real judgments citing Section
3(p), the Biological Diversity Act, or Ayurveda-specific IP disputes, verify
each one against the actual judgment text, and seed this collection properly. It
is entirely plausible this collection legitimately starts near-empty for the
MVP demo — the product statement itself frames case law as one of several
source types the corpus draws on, not a mandatory large category, and India
appears to have relatively little litigated case law specifically on 3(p) as
opposed to 3(d) (which has substantial case law, e.g. the well-known Novartis
Glivec litigation — that could be a legitimate first real case_law record if
someone verifies it against the actual judgment text before adding it here).
