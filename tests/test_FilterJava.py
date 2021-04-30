import os
import sys

import pytest

testFolder = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, testFolder + '/..')

import FilterJava


def testDeleteFile():
	lines = '''
diff --git a/test/org/mockito/internal/verification/RegisteredInvocationsTest.java b/test/org/mockito/internal/verification/RegisteredInvocationsTest.java
new file mode 100644
index 0000000..8168e59
--- /dev/null
+++ b/test/org/mockito/internal/verification/RegisteredInvocationsTest.java
@@ -0,0 +1,33 @@
+/*
+ * Copyright (c) 2007 Mockito contributors
+ * This program is made available under the terms of the MIT License.
+ */
'''

	lines2 = FilterJava.removeNonJava(lines.strip().splitlines())
	assert any(filter(lambda l: l.startswith('+++'), lines2)) == False
	assert any(filter(lambda l: l.startswith('---'), lines2)) == False


@pytest.mark.timeout(1)
def testModeChange():
	lines = '''
diff --git a/ReactAndroid/src/main/java/com/facebook/react/cxxbridge/ExecutorToken.java b/ReactAndroid/src/main/java/com/facebook/react/cxxbridge/ExecutorToken.java
new file mode 100644
index 0000000..e69de29
diff --git a/ReactAndroid/src/main/java/com/facebook/react/cxxbridge/JSBundleLoader.java b/ReactAndroid/src/main/java/com/facebook/react/cxxbridge/JSBundleLoader.java
new file mode 100644
index 0000000..09fd6a4
--- /dev/null
+++ b/ReactAndroid/src/main/java/com/facebook/react/cxxbridge/JSBundleLoader.java
@@ -0,0 +1,90 @@
+/**'''
	lines2 = FilterJava.removeNonJava(lines.strip().splitlines())
