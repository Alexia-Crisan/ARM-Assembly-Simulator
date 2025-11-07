    MOV R5, #5
    MOV R6, #7
    MOV R12, #6

; ----- INC / DEC / CLR -----
    INC R5              ; R5 = 6
    INC R5              ; R5 = 7
    DEC R5              ; R5 = 6
    CLR R6              ; R6 = 0
    OUT {R5, R6}

; ----- LSL: Logical Shift Left -----
    MOV R1, #3
    LSL R2, R1, #2      ; R2 = 3 * 4 = 12

    LSL R2, #1          ; R2 = 12 * 2 = 24

    OUT {R1, R2}

; ----- LSR: Logical Shift Right -----
    LSR R4, R2, #3      ; R4 = 24 / 8 = 3

    LSR R4, #1          ; R4 = 3 / 2 = 1

    OUT {R2, R4}

; ----- MOD: R7 = R5 % R3 -----
    MOV R5, #17
    MOV R3, #5
    MOD R7, R5, R3       ; R7 = 17 % 5 = 2

; ----- SWAP -----
    MOV R8, #15
    MOV R9, #1
    SWAP R8, R9
    SWP R9, R8

    OUT {R5, R3, R7}

    HLT
