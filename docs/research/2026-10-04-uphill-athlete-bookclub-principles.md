# Uphill Athlete book-club principles for the scheduler

Date: 2026-10-04 (Australia/Sydney). Status: research extraction for design review.

Source: [the supplied Evoke book-club playlist](https://www.youtube.com/playlist?list=PLuO4QS-PS1DfAqVMxkzR4GCumOB790Vuz).
All nine listed public videos yielded English auto-generated captions: about
10 hours 23 minutes and 107,438 caption words. Full captions were searched for
long-run and weekly-percentage language; selected surrounding passages were
read for the principles below. This is a focused scheduler distillation, not an
exhaustive chapter synopsis or a claim to have watched every frame.

Caption timestamps identify approximate passage starts. Automatic captions can
misrecognize technical terms and numbers; wording such as “Max CO2” in captions
must not become a new physiological term. Exact numeric prescriptions require
source confirmation before implementation. No long transcript passages are
reproduced. [The manifest](2026-10-04-bookclub-source-manifest.json) records video
IDs, caption hashes, retrieval method and reviewed windows.

## Long-run percentage: finding and limit

The supplied [individual video](https://www.youtube.com/watch?v=1emEMbVnYBo)
is titled Chapter 3. I did not locate an explicit weekly long-run percentage in
the retrieved captions, including the playlist-wide terminology search. That
does not prove there is none in a slide or a passage the captions misrecognize.

Two relevant passages are:

- [36:30](https://www.youtube.com/watch?v=1emEMbVnYBo&t=2190): maintain regular
  training instead of relying on occasional huge weekends that impair subsequent
  consistency; increase demands gradually and alternate loading with recovery.
- [1:01:24](https://www.youtube.com/watch?v=1emEMbVnYBo&t=3684): ultra-specific
  preparation need not reproduce the full event duration. The long-session
  examples are contextual, not universal ceilings or weekly proportions.

Therefore this source does not yet establish our app's 33%/30% single-long-run
caps, 50% combined weekend cap, or their denominator. Keep that attribution
unresolved. Do not change the caps merely because this caption search found no
support. A timestamp or slide containing the claimed percentage would allow a
precise follow-up.

## Extracted principles, with scope

### P1 — Assess the individual aerobic system

[Physiology, 32:19–34:30](https://www.youtube.com/watch?v=PP7GqpvIVWY&t=1939).
Scott explains distinct aerobic and anaerobic thresholds as useful landmarks
for understanding an athlete's response and planning training. The discussion
at [15:00](https://www.youtube.com/watch?v=PP7GqpvIVWY&t=900) connects endurance
with the properties of the recruited muscle fibers.

**Design inference:** intensity decisions should use individual measurements and
retain their provenance. A watch estimate or tier label does not establish an
athlete's true thresholds. Do not copy the presentation's simplified metabolic
illustrations into precise diagnostic claims.

### P2 — Aerobic support and threshold terminology matter

[Physiology part 2, 02:14–05:02](https://www.youtube.com/watch?v=twzUV-tdMs0&t=134)
describes aerobic capacity supporting the use of lactate as fuel. At
[13:27–16:13](https://www.youtube.com/watch?v=twzUV-tdMs0&t=807), Scott explains
that “lactate threshold” can mean different things across sources and requires
context.

**Design inference:** explicitly name AeT and AnT in the rule register. Do not
merge threshold definitions from different conventions or assume all lactate is
harmful. Separate an explanatory coaching model from a validated medical model.

### P3 — Use recovery feedback alongside metrics

[Monitoring training, 31:37–35:40](https://www.youtube.com/watch?v=iIyUMpFAx_A&t=1897).
Scott emphasizes perceived response and trends across good and bad days. He
describes reducing or stopping a session when the warm-up does not improve how
the athlete feels, rather than allowing a training score to override feedback.

**Design inference:** explicit fatigue/readiness feedback can justify adaptation;
a missing log alone cannot stand in for that feedback. Preserve why a plan was
reduced. A software volume floor must not force the athlete through a reported
recovery problem. This is coaching context, not an automatic diagnosis.

### P4 — Consistent, absorbable work beats copied elite workloads

[Application part 1, 38:53–41:27](https://www.youtube.com/watch?v=PrWqNDsKnHg&t=2333)
uses repeatability as a practical gauge for routine aerobic work and favors
starting conservatively. At
[41:29–43:55](https://www.youtube.com/watch?v=PrWqNDsKnHg&t=2489), Scott warns that
an elite athlete's recent training hides the years that made it tolerable.

**Scope:** the repeatability discussion concerns base work, not an order to
repeat every long run daily. **Design inference:** progression needs training
history and recovery context. Recreational and sub-elite labels should not
unlock elite session volumes or doubles on their own.

### P5 — A treadmill substitution can change the stimulus

[Application part 2, 12:44–15:22](https://www.youtube.com/watch?v=CmTg2Wcj1dM&t=764).
Scott discusses the difficulty of performing short maximal hill sprints on
machines that cannot change speed quickly. He suggests accessible stairs and
also discusses a longer machine alternative, explicitly recognizing its
changed character. At
[23:54–26:10](https://www.youtube.com/watch?v=CmTg2Wcj1dM&t=1434), recovery is
framed as enabling subsequent training, with individual recovery needs.

**Design inference:** do not treat every workout with “hill” in its title as the
same treadmill session. Distinguish sustained incline work, power repetitions
and ME. Stair access must be known; no-gym does not imply stairs are available.
The machine workaround is not a default app prescription and does not justify
instructions to jump onto a moving belt.

### P6 — VO2max is not a complete performance prescription

[High intensity/VO2max, 18:23–20:35](https://www.youtube.com/watch?v=UOG5cPN_vkQ&t=1103).
Scott distinguishes what VO2max changes can mean for untrained versus trained
athletes and discusses economy and threshold performance as other determinants.
The introductory discussion at
[02:10–03:16](https://www.youtube.com/watch?v=UOG5cPN_vkQ&t=130) cautions against
assuming one universally optimal interval format.

**Design inference:** use VO2max as one input, not permission to prescribe a
fixed high-intensity dose. Session choice must account for the athlete, event,
phase and recovery. This extraction does not change existing tier anchors.

### P7 — Strength, power and endurance are different qualities

[Strength and power, 02:36–05:04](https://www.youtube.com/watch?v=jardqEerNKQ&t=156)
distinguishes force production and its neural coordination from endurance.
At [31:10–33:55](https://www.youtube.com/watch?v=jardqEerNKQ&t=1870), Scott explains
why improving maximal strength is not a universal proxy for endurance performance
and declines to supply one universal strength benchmark.

**Design inference:** keep workout purpose explicit. Do not score a pure strength
circuit as running distance, or treat increasing weights as interchangeable
with increasing endurance. Do not infer a strength prerequisite solely from
weekly kilometers, VO2max or runner tier.

### P8 — Assess movement, then select suitable strength/power work

[Assessment/programming, 15:01–17:30](https://www.youtube.com/watch?v=htn5zPYg4HA&t=901)
describes increasingly demanding movement assessments. At
[33:18–36:05](https://www.youtube.com/watch?v=htn5zPYg4HA&t=1998), Scott discusses
power work after adequate general strength, with recovery between repetitions
and stopping when power declines.

**Design inference:** a power session must preserve repetition quality rather
than pursue exhaustion. The app should not infer successful movement assessment
from a race result, nor diagnose dysfunction from missing assessment data.
Appropriate surface, equipment and preparation are prerequisites.

## What this means for the Vietnam cases

The following are product-design applications, not verbatim instructions from
Scott or new claims of physiological equivalence:

| Scenario or failure | Proposed requirement | Validation example |
|---|---|---|
| Flat weekday outdoor access | Select accessible aerobic work; reserve mountain-specific work for permitted days | No weekday outdoor hill prescription in the no-gym fixture |
| Weekday gym access | Check the machine and session type before selecting incline work | Do not convert a power sprint to generic incline tempo solely by matching a title |
| No gym | Use only confirmed bodyweight/household equipment; stairs require separate confirmation | No added weights or assumed stair access |
| Weekend mountains | Evaluate the load and surrounding recovery in addition to day availability | Passing the access check does not establish a well-distributed week |
| Mixed ME and running | Account for movement segments once, while pure strength stays distinct | Warm-up/cool-down distance survives normalization |
| Unknown or missed training | Keep unknown, completed and explicitly missed states distinct | Completion override does not fabricate completed load |
| Poor readiness | Preserve a justified adaptation with its evidence | A weekly-distance gate does not override reported fatigue |
| Strength/power prescription | Keep purpose, prerequisites and stop conditions explicit | Exhaustion is not the success criterion for a power session |

## Source handling and next design decisions

- These notes summarize Scott's coaching explanations; they do not independently
  establish every physiological assertion in the talks.
- Retrieved captions stay temporary and outside the repository. The committed
  artifact contains paraphrases, links and provenance, not full transcripts.
- No KB import, scheduler seed change, prompt revision, environment-label move
  or production action is part of this extraction.
- Keep the previously verified ME set-order finding from Scott's written article
  alongside these talks; this extraction does not invent a new ME protocol.
- Before implementation, settle the long-run policy's units, population, phase
  and exceptions. The percentage question is still open rather than filled in
  from an unrelated running framework.
