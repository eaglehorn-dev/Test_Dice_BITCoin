import { useState } from "react"

export default function Footer() {


    return (
        <footer className="w-full bg-black gap-4 text-white flex flex-col items-center py-6">


            <img src="/assets/bitcoin-logo.svg" className="h-8" suppressHydrationWarning alt="Bitcoin" />
            <div className="text-center">
                <p className="text-white text-sm font-semibold">Bitcoin Dice</p>
            </div>
            <div>Copyright 2018
            </div>


        </footer>
    )
}
