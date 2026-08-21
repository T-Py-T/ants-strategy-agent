# GitRoll triage for revision `24b704b`

This document records the disposition of every finding opened from the GitRoll
scan of commit `24b704b751f9bf7c9edd9ba0f81568b44122742e`. The 63 issues contain
1,216 findings. `Strategy.java` is split across issues #7 and #8, so its 202
findings are counted once across those two issue bodies.

## Disposition policy

- Maintained Python paths receive safe correctness and maintainability fixes.
- Cognitive-complexity rewrites in the game engine, bot strategy, and seeded map
  algorithms are not performed without golden replay/map equivalence fixtures.
  Those rewrites can change game outcomes despite looking structural.
- Standalone map-generator prototypes receive safe syntax, naming, and data-
  structure cleanup. Seed-sensitive control flow, unfinished algorithms, CLI
  output, and default-package launch contracts remain explicitly dispositioned.
- `docs/reference/xathis/` is the preserved source of the 2011 winning bot. It is
  evidence for the partial Python reimplementation, not a maintained Java
  application.
- `src/sample_bots/` contains protocol opponents and deliberate failure fixtures
  (`ErrorBot`, `InvalidBot`, and `TimeoutBot`). Cross-language packaging and broad
  cleanup would weaken their value as original, directly executable fixtures.
- `visualizer/js/` is the bundled upstream legacy visualizer. Its global-script
  scoping and browser compatibility are coupled: mechanically replacing `var`,
  rewriting prototype code, or removing apparently dead branches is not safe
  without first creating a modern module build and replay-based browser suite.

## Roll-up

| Disposition | Findings | Result |
| --- | ---: | --- |
| Corrected in code | 251 | Correctness defects and safe smells removed; tests updated where interfaces changed. |
| Explicit engineering deferral | 72 | Seed/game-sensitive complexity or unfinished utility behavior; rationale recorded per issue below. |
| Preserved Xathis reference | 338 | Historical Java source remains byte-for-byte stable. |
| Preserved sample fixtures | 100 | Original multi-language opponents and deliberate protocol failures remain stable. |
| Preserved upstream visualizer | 455 | Legacy global-script/browser behavior remains stable. |
| **Total** | **1,216** | Every finding is either fixed or explicitly dispositioned. |

## Issue-by-issue disposition

| Issue | File | Findings | Disposition |
| --- | --- | ---: | --- |
| [#7](https://github.com/T-Py-T/ants-strategy-agent/issues/7) | `docs/reference/xathis/Strategy.java` (1/2) | 169 | Reference snapshot; preserved as the source for comparison with the partial Python reimplementation. |
| [#8](https://github.com/T-Py-T/ants-strategy-agent/issues/8) | `docs/reference/xathis/Strategy.java` (2/2) | 33 | Reference snapshot; preserved as the source for comparison with the partial Python reimplementation. |
| [#9](https://github.com/T-Py-T/ants-strategy-agent/issues/9) | `src/ants/ants.py` | 54 | Fixed 40 safe findings, including the identical attack branch and always-true comparison. Deferred 14 game-engine complexity rewrites pending golden replay equivalence. |
| [#10](https://github.com/T-Py-T/ants-strategy-agent/issues/10) | `src/sample_bots/java/Tile.java` | 2 | Fixed null-unsafe equality and made the override explicit. Kept the default package so the sample bot sources continue to compile and launch directly from their directory. |
| [#11](https://github.com/T-Py-T/ants-strategy-agent/issues/11) | `src/tools/mapgen/MapGenerator.java` | 24 | Fixed 21 findings: all three null paths plus 18 safe validation, naming, modifier, append, and array-copy smells. The start-position loop remains unchanged pending deterministic map equivalence; `System.out` is the API's requested map output, and the default package preserves direct sibling compilation. |
| [#12](https://github.com/T-Py-T/ants-strategy-agent/issues/12) | `src/tools/mapgen/McMaps.py` | 55 | Fixed 39 findings, including the Python 3 sort failure, shadowed builtins, no-op/debug blocks, unused locals and indices, type checks, and stale commented code. Deferred 16 behavior-sensitive or incomplete items: seven complexity rewrites, five TODO implementations, the unfinished Delaunay merge, and three unused settings in the unfinished `cell_maze` prototype. |
| [#13](https://github.com/T-Py-T/ants-strategy-agent/issues/13) | `src/tools/mapgen/SymmetricMapgen.java` | 25 | Fixed 23 findings: integer overflow plus unused fields, modifier order, redundant casts, boolean flow, and stack modernization. `System.out` is the standalone generator's CLI output, and the default package preserves direct launch. |
| [#14](https://github.com/T-Py-T/ants-strategy-agent/issues/14) | `visualizer/copy_paste.html` | 1 | Fixed the missing document language. |
| [#15](https://github.com/T-Py-T/ants-strategy-agent/issues/15) | `visualizer/js/CanvasElement.js` | 81 | Bundled upstream visualizer; preserved under the global-script compatibility policy above. |
| [#16](https://github.com/T-Py-T/ants-strategy-agent/issues/16) | `docs/reference/xathis/Ant.java` | 36 | Reference snapshot; preserved. |
| [#17](https://github.com/T-Py-T/ants-strategy-agent/issues/17) | `docs/reference/xathis/Connection.java` | 39 | Reference snapshot; preserved. |
| [#18](https://github.com/T-Py-T/ants-strategy-agent/issues/18) | `docs/reference/xathis/Direction.java` | 4 | Reference snapshot; preserved. |
| [#19](https://github.com/T-Py-T/ants-strategy-agent/issues/19) | `docs/reference/xathis/Logger.java` | 25 | Reference snapshot; preserved. |
| [#20](https://github.com/T-Py-T/ants-strategy-agent/issues/20) | `docs/reference/xathis/MyBot.java` | 1 | Reference snapshot; preserved. |
| [#21](https://github.com/T-Py-T/ants-strategy-agent/issues/21) | `docs/reference/xathis/Tile.java` | 28 | Reference snapshot; preserved. |
| [#22](https://github.com/T-Py-T/ants-strategy-agent/issues/22) | `docs/reference/xathis/Type.java` | 3 | Reference snapshot; preserved. |
| [#23](https://github.com/T-Py-T/ants-strategy-agent/issues/23) | `scripts/analyze_results.py` | 9 | Fixed all findings; split loading/normalization helpers, removed confusing strings/conditional, and removed the constant condition. |
| [#24](https://github.com/T-Py-T/ants-strategy-agent/issues/24) | `src/ants/engine.py` | 19 | Fixed 17 safe findings and centralized protocol-line literals. Deferred the two main loop complexity rewrites pending golden full-game equivalence. |
| [#25](https://github.com/T-Py-T/ants-strategy-agent/issues/25) | `src/ants/sandbox.py` | 5 | Fixed all findings. |
| [#26](https://github.com/T-Py-T/ants-strategy-agent/issues/26) | `src/bots/ants.py` | 6 | Fixed three safe findings. Deferred three protocol-parser/direction complexity rewrites to preserve the bot wire contract. |
| [#27](https://github.com/T-Py-T/ants-strategy-agent/issues/27) | `src/bots/bot.py` | 11 | Fixed nine safe findings, including explicit imports and idiomatic membership checks. Deferred two strategy complexity rewrites pending game-outcome equivalence. |
| [#28](https://github.com/T-Py-T/ants-strategy-agent/issues/28) | `src/bots/xathis_bot.py` | 17 | Fixed four safe findings and updated direct tests for the narrowed battle helper. Deferred 13 complexity rewrites because the incomplete reimplementation is behavior-sensitive and not validated against the historical winner. |
| [#29](https://github.com/T-Py-T/ants-strategy-agent/issues/29) | `src/sample_bots/java/Aim.java` | 5 | Multi-language reference opponent; preserved. |
| [#30](https://github.com/T-Py-T/ants-strategy-agent/issues/30) | `src/sample_bots/java/Ants.java` | 24 | Multi-language protocol/reference fixture; preserved. |
| [#31](https://github.com/T-Py-T/ants-strategy-agent/issues/31) | `src/sample_bots/java/Bot.java` | 2 | Multi-language protocol/reference fixture; preserved. |
| [#32](https://github.com/T-Py-T/ants-strategy-agent/issues/32) | `src/sample_bots/java/HunterBot.java` | 4 | Reference opponent; preserved. |
| [#33](https://github.com/T-Py-T/ants-strategy-agent/issues/33) | `src/sample_bots/java/Ilk.java` | 3 | Multi-language protocol/reference fixture; preserved. |
| [#34](https://github.com/T-Py-T/ants-strategy-agent/issues/34) | `src/sample_bots/java/LeftyBot.java` | 10 | Reference opponent; preserved. |
| [#35](https://github.com/T-Py-T/ants-strategy-agent/issues/35) | `src/sample_bots/java/RandomBot.java` | 3 | Reference opponent; preserved. |
| [#36](https://github.com/T-Py-T/ants-strategy-agent/issues/36) | `src/sample_bots/php/Ants.php` | 9 | Multi-language protocol/reference fixture; preserved. |
| [#37](https://github.com/T-Py-T/ants-strategy-agent/issues/37) | `src/sample_bots/php/HunterBot.php` | 3 | Reference opponent; preserved. |
| [#38](https://github.com/T-Py-T/ants-strategy-agent/issues/38) | `src/sample_bots/php/LeftyBot.php` | 3 | Reference opponent; preserved. |
| [#39](https://github.com/T-Py-T/ants-strategy-agent/issues/39) | `src/sample_bots/php/MyBot.php` | 2 | Reference opponent; preserved. |
| [#40](https://github.com/T-Py-T/ants-strategy-agent/issues/40) | `src/sample_bots/php/RandomBot.php` | 2 | Reference opponent; preserved. |
| [#41](https://github.com/T-Py-T/ants-strategy-agent/issues/41) | `src/sample_bots/python/ants.py` | 6 | Protocol/reference fixture shared by sample opponents; preserved. |
| [#42](https://github.com/T-Py-T/ants-strategy-agent/issues/42) | `src/sample_bots/python/ErrorBot.py` | 3 | Deliberately failing engine-error fixture; preserved. |
| [#43](https://github.com/T-Py-T/ants-strategy-agent/issues/43) | `src/sample_bots/python/GreedyBot.py` | 5 | Reference opponent; preserved. |
| [#44](https://github.com/T-Py-T/ants-strategy-agent/issues/44) | `src/sample_bots/python/HoldBot.py` | 2 | Reference opponent; preserved. |
| [#45](https://github.com/T-Py-T/ants-strategy-agent/issues/45) | `src/sample_bots/python/HunterBot.py` | 2 | Reference opponent; preserved. |
| [#46](https://github.com/T-Py-T/ants-strategy-agent/issues/46) | `src/sample_bots/python/InvalidBot.py` | 1 | Deliberately invalid engine-protocol fixture; preserved. |
| [#47](https://github.com/T-Py-T/ants-strategy-agent/issues/47) | `src/sample_bots/python/LeftyBot.py` | 6 | Reference opponent; preserved. |
| [#48](https://github.com/T-Py-T/ants-strategy-agent/issues/48) | `src/sample_bots/python/logutils.py` | 2 | Support code for sample/reference opponents; preserved. |
| [#49](https://github.com/T-Py-T/ants-strategy-agent/issues/49) | `src/sample_bots/python/RandomBot.py` | 2 | Reference opponent; preserved. |
| [#50](https://github.com/T-Py-T/ants-strategy-agent/issues/50) | `src/sample_bots/python/TimeoutBot.py` | 1 | Deliberately timing-out engine fixture; preserved. |
| [#51](https://github.com/T-Py-T/ants-strategy-agent/issues/51) | `src/tools/mapgen/asymmetric_mapgen.py` | 14 | Fixed all findings. |
| [#52](https://github.com/T-Py-T/ants-strategy-agent/issues/52) | `src/tools/mapgen/heightmap.py` | 5 | Fixed three safe findings. Deferred two seed-sensitive algorithm complexity rewrites pending golden map fixtures. |
| [#53](https://github.com/T-Py-T/ants-strategy-agent/issues/53) | `src/tools/mapgen/map.py` | 18 | Fixed 15 safe findings, including exception specificity and the swallowed indexing error. Deferred two complexity rewrites and the public `map` field rename because all generators depend on that interface. |
| [#54](https://github.com/T-Py-T/ants-strategy-agent/issues/54) | `src/tools/mapgen/mapgen.py` | 34 | Fixed all 28 mechanical findings. Deferred six seed-sensitive algorithm/CLI complexity rewrites pending golden map fixtures. |
| [#55](https://github.com/T-Py-T/ants-strategy-agent/issues/55) | `src/tools/mapgen/MapWalker.java` | 9 | Fixed eight safe modifier, cast, stack, and boolean-flow findings. Kept the default package because relocation would break direct compilation with sibling generators. |
| [#56](https://github.com/T-Py-T/ants-strategy-agent/issues/56) | `src/tools/mapgen/random_map.py` | 1 | Fixed the wildcard import. |
| [#57](https://github.com/T-Py-T/ants-strategy-agent/issues/57) | `src/tools/mapgen/symmetric_mapgen.py` | 8 | Fixed seven mechanical findings. Deferred one seed-sensitive algorithm complexity rewrite pending golden map fixtures. |
| [#58](https://github.com/T-Py-T/ants-strategy-agent/issues/58) | `src/tools/mapgen/Test.java` | 3 | Removed the stale commented-out call. `System.out` is the manual harness output, and the default package preserves direct sibling compilation. |
| [#59](https://github.com/T-Py-T/ants-strategy-agent/issues/59) | `src/tools/playgame.py` | 3 | Fixed the broad import catch and duplicate log-name literal. Deferred the monolithic CLI orchestration rewrite pending golden end-to-end games. |
| [#60](https://github.com/T-Py-T/ants-strategy-agent/issues/60) | `visualizer/js/Ant.js` | 10 | Bundled upstream visualizer; preserved under the compatibility policy above. |
| [#61](https://github.com/T-Py-T/ants-strategy-agent/issues/61) | `visualizer/js/Application.js` | 133 | Bundled upstream visualizer; preserved under the compatibility policy above. |
| [#62](https://github.com/T-Py-T/ants-strategy-agent/issues/62) | `visualizer/js/Buttons.js` | 34 | Bundled upstream visualizer; preserved under the compatibility policy above. |
| [#63](https://github.com/T-Py-T/ants-strategy-agent/issues/63) | `visualizer/js/Config.js` | 11 | Bundled upstream visualizer; preserved under the compatibility policy above. |
| [#64](https://github.com/T-Py-T/ants-strategy-agent/issues/64) | `visualizer/js/Const.js` | 16 | Bundled upstream visualizer; preserved under the compatibility policy above. |
| [#65](https://github.com/T-Py-T/ants-strategy-agent/issues/65) | `visualizer/js/Director.js` | 14 | Bundled upstream visualizer; preserved under the compatibility policy above. |
| [#66](https://github.com/T-Py-T/ants-strategy-agent/issues/66) | `visualizer/js/ImageManager.js` | 12 | Bundled upstream visualizer; preserved under the compatibility policy above. |
| [#67](https://github.com/T-Py-T/ants-strategy-agent/issues/67) | `visualizer/js/Replay.js` | 97 | Bundled upstream visualizer; preserved under the compatibility policy above. |
| [#68](https://github.com/T-Py-T/ants-strategy-agent/issues/68) | `visualizer/js/Util.js` | 36 | Bundled upstream visualizer; preserved under the compatibility policy above. |
| [#69](https://github.com/T-Py-T/ants-strategy-agent/issues/69) | `visualizer/js/visualizer.js` | 11 | Bundled upstream visualizer; preserved under the compatibility policy above. |

## Verification requirements

The maintained Python code-changing subset is covered by Python compilation,
pytest, static checks for fatal Python errors, and a short real game through
`playgame.py`. Focused regressions also pin the analyzer's exported-summary
enrichment and the historical random-number consumption in `McMaps.delaunay`
and `Map.tile`. CI does not compile Java, so the focused Java cleanup is checked
with Java syntax parsing and source review; lack of CI-backed compilation is an
explicit verification limitation. The entries dispositioned as preserved are
verified by confirming the diff does not alter them. The only changes within
those directory trees are the explicit `src/sample_bots/java/Tile.java`
correctness fix and `visualizer/copy_paste.html` accessibility fix described
above.
