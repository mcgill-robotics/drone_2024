# drone_2024
Use  `git clone <https-link>` to clone this repo.
Drone and various other models can be found under models.
README files can be found under the onboard_ws and off_board_ws folders which are relevant to their respective workspaces
# Packages structure
Please test abundantly, for each node write an equivalently named
test python script which tests the functionallity of that node and the 
various functions that can found there. Refer to [this tutorial for testing ros 2 code](https://docs.ros.org/en/humble/Tutorials/Intermediate/Testing/Testing-Main.html)

    \<pkg_name>
        \<pkg_name>
            <nodes.py>
        \tests
            <node_test.py>
        setup.cfg
        setup.py
        package.xml


