; Input: N in R0
; Output: factorial in R1, two divisions in R2 and R3

        MOV     R0, #5
        MOV     R1, #1      ; factorial = 1
        MOV     R2, #1      ; counter = 1
        MOV     R4, R0      ; copy N to R4 for loop

        ADD     R0, #1

factorial_loop:
        MUL     R1, R2  ; factorial *= counter
        ADD     R2, #1  ; counter++

        CMP     R2, R0      ; compare counter with N
        BNE factorial_loop 
        B factorial_done

factorial_done:

        MOV     R5, #3
        DIV     R6, R1, R5  ; R2 = factorial / 3

        MOV     R7, #21
        DIV     R7, R5

        STR     R1, [R10]    ; factorial
        STR     R2, [R10, #4] ; first division
        STR     R7, [R10, #8] ; second division

        HLT