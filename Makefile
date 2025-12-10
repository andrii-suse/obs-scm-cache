SHELL := /bin/bash

test:
	for f in t/environ/*.sh ; do bash -x $$f && continue; echo FAIL: $$f; break; done

test_container:
	( cd t/environ; for f in *.sh; do echo starting $$f; ./$$f && continue; echo FAIL $$f; break; done )

test_container_manual:
	( cd t/manual; for f in *.sh; do echo starting $$f; ./$$f && continue; echo FAIL $$f; break; done )

test_manual:
	for f in t/manual/*.sh ; do bash -x $$f && continue; echo FAIL: $$f; break; done

