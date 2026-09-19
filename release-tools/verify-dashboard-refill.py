"""Run the existing refill suite after a pending Web Animation pause has settled.

Animation.playState may already be 'paused' while Animation.pending is still
true. Sampling currentTime in that interval compares a pending timeline with
the final holdTime. Wait for the pause operation to commit; do not skip or relax
any clock, board, visual frame, resume, or currentTime equality assertion.
This changes the test only, never the delivered game bundle.
"""
from pathlib import Path

source = Path(__file__).resolve().parents[1] / 'scripts' / 'verify-burst-refill.py'
text = source.read_text()
before = 'page.wait_for_function(ANIMS+".every(a=>a.playState===\'paused\')")'
after = 'page.wait_for_function(ANIMS+".every(a=>a.playState===\'paused\' && !a.pending)")'
assert text.count(before) == 1, 'Refill verifier changed; review pause synchronization before running'
text = text.replace(before, after)
exec(compile(text, str(source), 'exec'), {'__name__': '__main__', '__file__': str(source)})
