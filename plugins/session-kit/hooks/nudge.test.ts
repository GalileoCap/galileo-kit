import { expect, test } from 'claude-code/testing'

import { world } from './world.test-helper'

const single = `python3 - <<'EOF'
from pathlib import Path
p = Path('README.md')
s = p.read_text()
s = s.replace('old', 'new')
p.write_text(s)
EOF`

const twoReplaces = single.replace("s = s.replace('old', 'new')", "s = s.replace('old', 'new')\ns = s.replace('a', 'b')")
const regex = single.replace("s = s.replace('old', 'new')", "import re\ns = re.sub('o.d', 'new', s)")
const manyFiles = single.replace("p = Path('README.md')", "for p in Path('docs').glob('*.md'):\n    pass\np = Path('README.md')")
const shell = `cat > README.md <<'EOF'\nnew\nEOF`

test('a Python heredoc doing one read, one replace and one write is told to use the Edit tool', async ($, on) => {
  world(on)
  on('tool.call', () => ({ result: { stdout: '', stderr: '', interrupted: false } }))

  const ran = await $.tool.call({ tool: 'Bash', command: single })
  expect(ran.context?.length).toBe(1)
  expect(ran.context?.[0]).toMatch(/Edit tool/)
})

test('two replaces, a regex, several files or a shell heredoc get no nudge', async ($, on) => {
  world(on)
  on('tool.call', () => ({ result: { stdout: '', stderr: '', interrupted: false } }))

  for (const command of [twoReplaces, regex, manyFiles, shell, 'python3 -c "print(1)"']) {
    expect((await $.tool.call({ tool: 'Bash', command })).context).toBeUndefined()
  }
})
