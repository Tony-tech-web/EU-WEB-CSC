import turtle
turtle.bgcolor("black")

squary = turtle.Turtle()
squary.speed(30)
squary.pencolor("Red")
for i in range(350):
    squary.forward(i)
    squary.left(100)
    squary.right(90)
    squary.forward(50)
    squary.left(70)
    
    