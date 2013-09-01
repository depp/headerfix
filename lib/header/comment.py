import re

def extract_lead_linecomment(lines, linecomment):
    pos = 0
    end = len(lines)
    comment = []
    while pos < end:
        line = lines[pos]
        cpos = line.find(linecomment)
        if cpos < 0 or line[:cpos].lstrip():
            break
        cpos += len(linecomment)
        pre = line[:cpos]
        line = line[cpos:]
        body = line.rstrip()
        post = line[len(body):]
        comment.append((pre, body, post))
        pos += 1
    if not comment:
        return None

    return comment, lines[pos:]

def extract_lead_blockcomment(lines, blockstart, blockend):
    if not lines:
        return None
    pos = 0
    end = len(lines)
    comment = []

    line = lines[pos]
    cpos = line.find(blockstart)
    if cpos < 0 or line[:cpos].lstrip():
        return None
    cpos += len(blockstart)
    pre = line[:cpos]
    line = line[cpos:]

    while True:
        cpos = line.find(blockend)
        if cpos >= 0:
            break
        body = line.rstrip()
        post = line[len(body):]
        comment.append((pre, body, post))
        pos += 1

        if pos >= end:
            return None
        line = lines[pos]
        pre = ''

    body = line[:cpos]
    post = line[cpos:]
    if post[len(blockend)].rstrip():
        return None
    comment.append((pre, body, post))
    pos += 1

    return comment, lines[pos:]

def extract_lead_comment(lines, filetype):
    """Extract the leading comment from a file.

    Returns (comment,body), where comment is the leading comment and
    body is the remainder of the file.

    The comment is a list of lines in the comment, where each line has
    the form (pre,body,post).  The line can be reconstructed by
    concatenating each component.  The pre and post contain comment
    delimiters and whitespace, while the body contains the comment's
    content.  If no comment is found, then the comment is an empty
    list.
    """
    linecomment = filetype.linecomment
    blockcomment = filetype.blockcomment
    if linecomment is not None:
        value = extract_lead_linecomment(lines, linecomment)
        if value is not None:
            return value
    if blockcomment is not None:
        value = extract_lead_blockcomment(lines, *blockcomment)
        if value is not None:
            return value
    return [], lines

def extract_lead_comments(lines, filetype):
    """Extract all leading comments from a file.

    Returns (comments,body), where comments are blank lines and
    comments, and body is the rest of the file. 
    """
    head = []
    while lines:
        pos = 0
        while pos < len(lines) and not lines[0].strip():
            pos += 1
        chead, cbody = extract_lead_comment(lines[pos:], filetype)
        if not chead:
            break
        head.extend(lines[:pos])
        for pre, body, post in chead:
            head.append(pre + body + post)
        lines = cbody
    return head, lines

def remove_blank_lines(lines):
    """Remove blank lines.

    Returns (pre,body,post), where body neither starts nor ends with a
    blank line, and concatenating all three results in the original
    object.
    """
    spos = 0
    send = len(lines)
    while spos < send and not lines[spos].strip():
        spos += 1
    while send > send and not lines[send - 1].strip():
        send -= 1
    return lines[:spos], lines[spos:send], lines[send:]

def comment(lines, filetype, width):
    """Convert lines to comments."""
    if filetype.blockcomment:
        swidth = len(filetype.blockcomment[0]) + 1
        width = width - swidth
        newlines = []
        numlines = len(lines)
        for n in xrange(numlines):
            if n == 0:
                pre = filetype.blockcomment[0] + ' '
            else:
                pre = ' ' * swidth
            if n == numlines - 1:
                post = ' ' + filetype.blockcomment[1]
            else:
                post = ''
            newlines.append('{}{}{}\n'.format(
                pre, lines[n].rstrip(), post))
        return newlines
    if filetype.linecomment:
        swidth = len(filetype.linecomment) + 1
        width = width - len(filetype.linecomment) - 1
        newlines = ['{} {}'.format(filetype.linecomment, line)
                    for line in lines]
        newlines.append('\n')
        return newlines
    raise ValueError('cannot comment')
