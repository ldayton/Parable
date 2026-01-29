//go:build ignore

package main

import (
	"os"
	"runtime/pprof"
)

func init() {
	f, _ := os.Create("/tmp/cpu.prof")
	pprof.StartCPUProfile(f)
}

func cleanup() {
	pprof.StopCPUProfile()
}
