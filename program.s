; simple program
start:
    MOV R0, #5
    MOV R1, #7
    ADD R2, R0, R1
    STR R2, [R3, #16]
    ;B start
