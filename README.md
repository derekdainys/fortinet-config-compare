Config Compare
===
A lot of traditional tools lack the ability to manage fortinet configurations effectively.

They either provide a way to add elements or to remove them from the configuration.

This is a tool that can take two configurations(running and candidate) and show the exact path needed
to go from the running configuration to candidate configuration. Including removing unnecessary elements.

It only provides the path needed to make the change on the device. It does not push configurations to devices
this would need to be handled by some other library or tool.

Examples
---
You may find some  example configurations are provided in the ```configs``` folder.

The focus will be on the BGP part of the configuration.

The running configuration that may be found in ```configs/running.conf```
```
config router bgp
    set as 65000
    set router-id 10.0.0.1
    set graceful-restart enable
    config neighbor
        edit "3.3.3.3"
            set remote-as 3
        next
    end
end
```
Now let's say we want to alter the configuration to the one found in ```configs/candidate.conf```
```
config router bgp
    set as 65000
    set router-id 10.0.0.2
    config neighbor
        edit "1.1.1.1"
            set remote-as 1
            set soft-reconfiguration enable
        next
        edit "2.2.2.2"
            set remote-as 2
            set soft-reconfiguration enable
            set bfd enable
        next
    end
end
```
Some elements need to be updated, some removed, and some added.

Suppose you have a simple example like the one found in ```example_1.py```
```python
print(config_compare(running="configs/running.conf", candidate="configs/candidate.conf"))
```
It would produde an output as such
```
config router bgp
    config neighbor
        edit "1.1.1.1"
            set remote-as 1
            set soft-reconfiguration enable
        next
        edit "2.2.2.2"
            set bfd enable
            set remote-as 2
            set soft-reconfiguration enable
        next
        delete "3.3.3.3"
    end
    set router-id 10.0.0.2
    unset graceful-restart
end
```

Which when applied to the running configuration will turn it into the candidate configuration.

For additional examples please view ```example_arg.py``` on how you might use arguments to pass in files, as well as generate
a revert configuration.

Features
---
Config Compare function has an option to change indentation if a different spacing is required.

Default is always set to **indent=4** which should match the fortinet output.

Some use cases may be readability when possibly a different indentation is wanted, or pushing configurations
to devices as there would be no need to provide actual spacing.

This can be adjusted as such:

```python
config_compare(running="configs/running.conf", candidate="configs/candidate.conf", indent=0)
```

This may be useful when pushing configurations to devices, but not actually looking at differences.


