#!/usr/bin/env rdmd

// Round floating point numbers
import std.algorithm, std.conv, std.functional,
    std.math, std.regex, std.stdio;

int[] hist = new int[5001];

int count(char[] line) {
	double delay = to!double(line);
	int d = cast(int)(round(delay*100));
	if(d>=hist.length)
		d=hist.length-1;

	hist[d]++;
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
