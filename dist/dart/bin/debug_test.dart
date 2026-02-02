import 'package:parable/parable.dart' as parable;

void main() {
  try {
    // Simple case
    print('Testing: echo hello');
    final nodes = parable.parse('echo hello', false);
    print('Result: ${nodes.length} nodes');
    for (final n in nodes) {
      print(n.toSexp());
    }
  } catch (e, s) {
    print('Error: $e');
    print('Stack trace:');
    print(s);
  }
}
