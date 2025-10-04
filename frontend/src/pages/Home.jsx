

function Home() {
    return(
        <>
        <p className="text-2xl">Expenss Management</p>
        <div className="h-dvh w-dvw flex flex-col justify-center items-center gap-4">
            <div className="border-2 border-black p-4 rounded-lg text-center h-fit w-fit">
                <button className="border-1 border-black p-2 rounded">Admin</button>
                <br />
                <button className="border-1 border-black p-2 rounded">Manager</button>
                <br />
                <button className="border-1 border-black p-2 rounded">Employee</button>
            </div>
        </div>
        </>
    )
}

export default Home;
