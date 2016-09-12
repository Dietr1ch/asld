#!/usr/bin/env rdmd

// Round floating point numbers
import std.algorithm, std.conv, std.functional,
    std.math, std.regex, std.stdio;

immutable auto resolutionInv = 1/0.01;  // 0.01s -> 100
int[] hist = new int[1+10*resolutionInv];

int count(char[] line) {
	double delay = to!double(line); // 0.4299
	int d = cast(int)(round(delay*resolutionInv)); // 42.999; 43
	if(d>=hist.length)
		d=hist.length-1;

	hist[d]++;  // Vote for 0.43s  (index 43)
	return 1;
}

void main() {
	stdin.byLine.map!count;

	foreach(line; stdin.byLine)
		count(line);

	int sum = 0;
	writef("[\n");
	foreach(int i, int c; hist)
		writef("%d,\n", sum+=c);
	writef("]\n");
}
