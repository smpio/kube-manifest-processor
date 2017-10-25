package main

import (
    "os"
    "log"
    "flag"
    "io/ioutil"

    "github.com/ghodss/yaml"
)

func main() {
    outDir := flag.String("dir", "", "output directory")
    flag.Parse()
    //glog.Info("Prepare to repel boarders")

    if *outDir == "" {
        log.Fatalln("No out dir")
        return
    }

    os.RemoveAll(*outDir)

    data, err := ioutil.ReadAll(os.Stdin)
    if err != nil {
        log.Fatalf("Error reading stdin: %v\n", err)
        return
    }

    var obj interface{}
    err = yaml.Unmarshal(data, &obj)
    if err != nil {
        log.Fatalf("Error parsing YAML: %v\n", err)
        return
    }

    data, err = yaml.Marshal(obj)
    if err != nil {
        log.Fatalf("Error formatting YAML: %v\n", err)
        return
    }

    os.Stdout.Write(data)
}
