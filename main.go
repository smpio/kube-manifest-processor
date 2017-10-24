package main

import (
    "os"
    "fmt"
    //"flag"
    "io/ioutil"

    //"github.com/golang/glog"
    "github.com/ghodss/yaml"
)

func main() {
    //flag.Parse()
    //glog.Info("Prepare to repel boarders")

    data, err := ioutil.ReadAll(os.Stdin)
    if err != nil {
        fmt.Printf("Error reading stdin: %v\n", err)
        return
    }

    var obj interface{}
    err = yaml.Unmarshal(data, &obj)
    if err != nil {
        fmt.Printf("Error parsing YAML: %v\n", err)
        return
    }

    data, err = yaml.Marshal(obj)
    if err != nil {
        fmt.Printf("Error formatting YAML: %v\n", err)
        return
    }
    os.Stdout.Write(data)
}
