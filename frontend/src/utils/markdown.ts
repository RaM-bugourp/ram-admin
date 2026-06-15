/**
 * 极简 Markdown 渲染器（不引入外部依赖）.
 *
 * 支持的子集：
 *   - 标题 # ~ ###
 *   - 粗体 **x** / 斜体 *x* / 行内代码 `x`
 *   - 无序列表 - / 有序列表 1.
 *   - 表格 | a | b |
 *   - 代码块 ```...```
 *   - 换行
 *
 * 注意：输出前已做 HTML 转义，避免 XSS。
 */

function escapeHtml(s: string): string {
    return s
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;')
}

function inline(text: string): string {
    // 行内：粗体 → 斜体 → 行内代码
    return text
        .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
        .replace(/\*([^*]+)\*/g, '<em>$1</em>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
}

export function renderMarkdown(src: string): string {
    if (!src) return ''
    const lines = src.split('\n')
    const html: string[] = []
    let i = 0

    while (i < lines.length) {
        const line = lines[i]

        // 代码块
        if (line.trim().startsWith('```')) {
            const lang = line.trim().slice(3)
            const buf: string[] = []
            i++
            while (i < lines.length && !lines[i].trim().startsWith('```')) {
                buf.push(escapeHtml(lines[i]))
                i++
            }
            i++ // skip closing ```
            html.push(`<pre><code${lang ? ` class="lang-${escapeHtml(lang)}"` : ''}>${buf.join('\n')}</code></pre>`)
            continue
        }

        // 标题
        const h = line.match(/^(#{1,6})\s+(.*)$/)
        if (h) {
            const level = h[1].length
            html.push(`<h${level}>${inline(escapeHtml(h[2]))}</h${level}>`)
            i++
            continue
        }

        // 表格（当前行以 | 开头，且下一行是分隔行 |---|）
        if (line.trim().startsWith('|') && i + 1 < lines.length && /^\s*\|[\s:|-]+\|\s*$/.test(lines[i + 1])) {
            const header = splitRow(line)
            i += 2
            const rows: string[][] = []
            while (i < lines.length && lines[i].trim().startsWith('|')) {
                rows.push(splitRow(lines[i]))
                i++
            }
            const thead = '<tr>' + header.map((c) => `<th>${inline(escapeHtml(c))}</th>`).join('') + '</tr>'
            const tbody = rows
                .map((r) => '<tr>' + r.map((c) => `<td>${inline(escapeHtml(c))}</td>`).join('') + '</tr>')
                .join('')
            html.push(`<table><thead>${thead}</thead><tbody>${tbody}</tbody></table>`)
            continue
        }

        // 无序列表
        if (/^\s*[-*]\s+/.test(line)) {
            const items: string[] = []
            while (i < lines.length && /^\s*[-*]\s+/.test(lines[i])) {
                items.push(`<li>${inline(escapeHtml(lines[i].replace(/^\s*[-*]\s+/, '')))}</li>`)
                i++
            }
            html.push(`<ul>${items.join('')}</ul>`)
            continue
        }

        // 有序列表
        if (/^\s*\d+\.\s+/.test(line)) {
            const items: string[] = []
            while (i < lines.length && /^\s*\d+\.\s+/.test(lines[i])) {
                items.push(`<li>${inline(escapeHtml(lines[i].replace(/^\s*\d+\.\s+/, '')))}</li>`)
                i++
            }
            html.push(`<ol>${items.join('')}</ol>`)
            continue
        }

        // 空行
        if (!line.trim()) {
            i++
            continue
        }

        // 普通段落
        html.push(`<p>${inline(escapeHtml(line))}</p>`)
        i++
    }

    return html.join('\n')
}

function splitRow(line: string): string[] {
    const trimmed = line.trim().replace(/^\|/, '').replace(/\|$/, '')
    return trimmed.split('|').map((c) => c.trim())
}
