"""Bounded read-only AT-SPI worker for one launched Firefox PID/local URL.

Run as a bounded subprocess: an inaccessible/hung desktop must never hang broker.
No text is read from other applications, browser chrome or unmatched documents.
"""
import json
import sys


def read_document(desktop, browser_pid, expected_url):
    applications = []
    for index in range(min(desktop.get_child_count(), 256)):
        application = desktop.get_child_at_index(index)
        if application is not None and application.get_process_id() == browser_pid:
            applications.append(application)
    visited = 0
    documents = []
    def find(node, depth=0):
        nonlocal visited
        visited += 1
        if visited > 512 or depth > 16:
            raise ValueError('browser_accessibility_tree_limit')
        document = node.get_document_iface()
        if document is not None:
            url = document.get_document_attribute_value('DocURL')
            if url == expected_url:
                documents.append(node)
                return
            if url:
                return  # foreign documents/iframes are never a traversal root
        for index in range(min(node.get_child_count(), 512)):
            child = node.get_child_at_index(index)
            if child is not None:
                find(child, depth + 1)
    for application in applications:
        find(application)
    if len(documents) != 1:
        raise ValueError('browser_scoped_document_not_ready')
    root = documents[0]
    chunks = []
    remaining = 16384
    def text(node, depth=0):
        nonlocal remaining, visited
        visited += 1
        if visited > 1024 or depth > 16:
            raise ValueError('browser_accessibility_tree_limit')
        document = node.get_document_iface()
        if document is not None:
            url = document.get_document_attribute_value('DocURL')
            if url and url != expected_url:
                return
        interface = node.get_text_iface()
        if interface is not None and remaining:
            count = interface.get_character_count()
            if count:
                value = interface.get_text(0, min(count, remaining))
                chunks.append(value)
                remaining -= len(value)
                return  # avoid counting descendants' text again
        for index in range(min(node.get_child_count(), 512)):
            if not remaining:
                break
            child = node.get_child_at_index(index)
            if child is not None:
                text(child, depth + 1)
    text(root)
    if root.get_document_iface().get_document_attribute_value('DocURL') != expected_url:
        raise ValueError('browser_document_changed')
    value = '\n'.join(chunks)
    if not value:
        raise ValueError('browser_document_text_unavailable')
    # UTF-8 bytes, rather than Python characters, define the IPC text budget.
    encoded = value.encode('utf-8', errors='strict')[:32768]
    value = encoded.decode('utf-8', errors='ignore')
    return {'untrusted': True, 'browser_pid': browser_pid, 'url': expected_url, 'text': value}


def main():
    try:
        import gi
        gi.require_version('Atspi', '2.0')
        from gi.repository import Atspi
        Atspi.init()
        # Native D-Bus calls also have a bound; parent imposes a whole-worker
        # deadline and discards stderr so private desktop data cannot leak there.
        Atspi.set_timeout(1000, 1000)
        result = read_document(Atspi.get_desktop(0), int(sys.argv[1]), sys.argv[2])
    except Exception:
        print(json.dumps({'error': 'browser_scoped_accessibility_unavailable'}))
        return 2
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
