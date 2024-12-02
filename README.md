FLL: City Shaper (2019-2020)
https://www.firstlegoleague.org/

In the FLL competition teams have to build a robot to solve various tasks on a mission table.
This repo contains the codes written for our robot.


If you are not familiar with EV3 robots or programming in general, here are some useful information to help you understand or use the code.

First of all, the EV3 MicroPython documentation: https://ev3dev-lang.readthedocs.io/projects/python-ev3dev/en/ev3dev-stretch/upgrading-to-stretch.html

It is important to note that, although the program is specific to the 2019 FLL mission table and our robot, some parts can be used in other cases. The first functions are quite universal (from 'returnGombok' to 'end,' from line 45 to 185). 'run1' - 'run4' (lines 188 - 305) are the functions where the robot solves tasks on the table. The 'manual' (lines 309 - 345) is a launch system based on the built-in buttons, and the while True loop is our final launch system powered by one of the color sensors. By making a few edits, you can easily use both the manual and the automated launch systems for starting your programs on an EV3 robot. (We used a (hardcoded ._.) .txt file to track time (ido.txt), because in the tournament it was crucial to be as time-efficient as possible. However, you can simply delete it if you do not need such a feature.)

On an EV3 robot, there are 4 inputs (used for sensors) and 4 outputs (used for motors). We used 2 large motors for the wheels and 2 medium motors for modular movements (we used different arms, frames, etc. to solve various tasks on the table), a gyrosensor, 2 color sensors facing downwards, and one additional color sensor which we used in our launch system to detect the current module and choose the appropriate run.
You can change the input and output settings in lines 16 - 25 and the sensor settings in lines 30-32.

The variable debug is used in many functions. If something isn't working properly, set it to True to enable debugging. This will display sensor or motor values in the terminal, helping you identify and resolve the problem.

The while True loop at the end might seem ugly, but since it's a launch system that is written for a microcontroller, after initialization we don't want our program to run just once, but until we cut it off. It's a pretty common solution.

For further explanation and documentation, check out the comments in main.py, and if something looks like it makes no sense, it's probably written in Hungarian. Sorry for that,,, but feel free to get in touch if needed! :)
