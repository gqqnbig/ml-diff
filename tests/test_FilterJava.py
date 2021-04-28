import os
import sys

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
