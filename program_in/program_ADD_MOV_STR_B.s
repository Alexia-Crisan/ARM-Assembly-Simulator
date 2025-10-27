; simple program
start:
    MOV R0, #5
    MOV R1, #7
    ADD R2, R0, R1
    STR R2, [R3, #16]
    B add
add:
    MOV R3, #4
    ADD R4, R0, R3
HLT