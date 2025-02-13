
# draw a ninja
import turtle

ninja = turtle.Turtle()
ninja.speed(100)

for i in range(60):
    ninja.forward(180)
    ninja.right(30)
    ninja.forward(90)
    ninja.left(60)
    ninja.forward(50)
    ninja.right(30)

    ninja.right(9)
    
    ninja.penup()
    ninja.setposition(0, 5)
    ninja.pendown()
     
turtle.done