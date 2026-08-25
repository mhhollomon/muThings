# Templates

You can define a template with replaceable parameters and then "render" the template with particular values.

It is all done via textual substitution.

So all variables are effectively strings and can be quoted. The
quotes will not be placed in the generated code.
```
template my_template(i,c) <{
    image b$i {
        size = scale, 0.9
        position = "attach($p, right, 60%, mid, 5)"
        color = "hsv($c, 90%, 90%)"
    }
}>

image starter {
    size = 200x200
    position = "output(30%, mid, min, min)"
}

render my_template(1, 120, p=starter)
render my_template(2, 180)
```

The variable `p` is reserved and stands for the name of the
element generated in the previous template call (even if
it was a different template)
