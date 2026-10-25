// McCabe complexity per function of every .ts/.tsx file under a directory (ui/ skipped).
const ts = require(process.argv[2]);
const fs = require('fs'), path = require('path');
const root = process.argv[3];
const files = [];
(function walk(d) { for (const e of fs.readdirSync(d, { withFileTypes: true })) {
  const p = path.join(d, e.name);
  if (e.isDirectory()) { if (e.name !== 'ui' && e.name !== 'node_modules') walk(p); }
  else if (/\.tsx?$/.test(e.name) && !/\.test\.tsx?$/.test(e.name)) files.push(p);
} })(root);
const isFn = n => ts.isFunctionDeclaration(n) || ts.isFunctionExpression(n) || ts.isArrowFunction(n) || ts.isMethodDeclaration(n) || ts.isGetAccessor(n) || ts.isSetAccessor(n) || ts.isConstructorDeclaration(n);
const out = [];
for (const f of files) {
  const src = ts.createSourceFile(f, fs.readFileSync(f, 'utf8'), ts.ScriptTarget.Latest, true);
  const visit = (n, fn) => {
    if (isFn(n)) { fn = { file: path.relative(root, f), line: src.getLineAndCharacterOfPosition(n.getStart()).line + 1, cc: 1, jsx: 0 }; out.push(fn); }
    else if (fn) {
      if (ts.isIfStatement(n) || ts.isConditionalExpression(n) || ts.isForStatement(n) || ts.isForInStatement(n) || ts.isForOfStatement(n) || ts.isWhileStatement(n) || ts.isDoStatement(n) || ts.isCatchClause(n) || ts.isCaseClause(n)) fn.cc++;
      if (ts.isBinaryExpression(n) && [ts.SyntaxKind.AmpersandAmpersandToken, ts.SyntaxKind.BarBarToken, ts.SyntaxKind.QuestionQuestionToken].includes(n.operatorToken.kind)) fn.cc++;
      if ((ts.isJsxElement(n) || ts.isJsxSelfClosingElement(n))) fn.jsx++;
    }
    ts.forEachChild(n, c => visit(c, fn));
  };
  visit(src, null);
}
const v = out.map(o => o.cc).sort((a, b) => a - b), jsx = out.reduce((s, o) => s + o.jsx, 0);
const sum = v.reduce((a, b) => a + b, 0);
console.log(JSON.stringify({ files: files.length, funcs: v.length, total: sum, mean: +(sum / v.length).toFixed(2), median: v[v.length >> 1], ge6: v.filter(x => x >= 6).length, ge11: v.filter(x => x >= 11).length, max: v[v.length - 1], jsxElements: jsx }));
