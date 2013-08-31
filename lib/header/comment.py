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
    if filetype is not None:
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
