use std::io::Result;

fn main() -> Result<()> {
    // Compile protobuf definitions
    tonic_build::configure()
        .build_server(true)
        .build_client(true)
        .out_dir("src/proto")
        .compile(&["../proto/colosseo.proto"], &["../proto"])?;
    
    println!("cargo:rerun-if-changed=../proto/colosseo.proto");
    Ok(())
}
