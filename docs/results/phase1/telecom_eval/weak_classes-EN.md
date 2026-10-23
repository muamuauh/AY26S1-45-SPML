# Weak classes (phase 2 generation targets)

> 中文版：[weak_classes.md](weak_classes.md)

The 4 classes with the lowest AP50 of E2 (mean of 3 seeds) on TelecomEval. Phase 2's (M3) risk-scenario specification covers these classes first.

| Rank | Class | AP50 | Training instances | Likely reason (filled by hand) |
|---|---|---|---|---|
| 1 | no_helmet | 0.141 ± 0.009 | 1047 | Few training samples; people in telecom photos are mostly far away or up a tower, so heads are small and caps, hoods and hair are hard to tell apart (presumed) |
| 2 | vehicle | 0.264 ± 0.089 | 244 | Fewest training instances, mostly site trucks; telecom sites have vans and pickups (presumed) |
| 3 | machinery | 0.269 ± 0.040 | 762 | Training machinery is mostly excavators and loaders; telecom bucket trucks, cable-pulling rigs and cable-drum trailers are rare (presumed) |
| 4 | harness | 0.299 ± 0.051 | 2619 | Work at Height is mostly scaffolding and aerial platforms; harnesses on poles and towers look different (presumed) |
