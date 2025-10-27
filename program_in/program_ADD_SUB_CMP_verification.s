        ; Test program for ADD, SUB, CMP (2- and 3-operand forms)
        ; Uses R0–R7, ends with HLT

        MOV     R0, #10          ; R0 = 10
        MOV     R1, #5           ; R1 = 5
        MOV     R2, #2           ; R2 = 2
        MOV     R10, R1          ; R10 = 5

        ; ---------- ADD ----------
        ADD     R3, R0, R1       ; R3 = 10 + 5 = 15
        ADD     R4, R3, #7       ; R4 = 15 + 7 = 22
        ADD     R5, R4           ; R5 = R5 + R4 (initially 0 + 22 = 22)
        ADD     R5, #3           ; R5 = 22 + 3 = 25  (+= immediate)

        ; ---------- SUB ----------
        SUB     R6, R4, R2       ; R6 = 22 - 2 = 20
        SUB     R7, R6, #10      ; R7 = 20 - 10 = 10
        SUB     R7, R1           ; R7 = 10 - 5 = 5
        SUB     R7, #2           ; R7 = 5 - 2 = 3

        ; ---------- CMP ----------
        CMP     R0, R1           ; Compare 10 vs 5  -> N = 0, Z = 0
        CMP     R1, R0           ; Compare 5 vs 10 -> N = 1, Z = 0
        CMP     R7, #3           ; Compare 3 vs 3  -> Z = 1
        CMP     R6, #20          ; Compare 20 vs 20 -> Z = 1
        CMP     R3, #0           ; Compare 15 vs 0  -> N = 0, Z = 0

        ; ---------- End of test ----------
        HLT                     ; Stop simulation
