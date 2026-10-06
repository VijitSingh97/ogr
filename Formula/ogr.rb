class Ogr < Formula
  desc "Open a Git repository's remote URL in your browser"
  homepage "https://github.com/VijitSingh97/ogr"
  url "https://github.com/VijitSingh97/ogr/archive/refs/tags/v0.0.1.tar.gz"
  sha256 "3d0adeb086b3d6949eb7c0816d1085cbc17bc106c2ce453ea27ad74081061b08"
  license "MIT"

  depends_on "python@3.13"
  uses_from_macos "git"

  def install
    inreplace "bin/ogr", "#!/usr/bin/env python3", "#!#{formula_opt_bin("python@3.13")}/python3.13"
    bin.install "bin/ogr"
    bash_completion.install "completions/ogr.bash" => "ogr"
    zsh_completion.install "completions/_ogr"
  end

  test do
    assert_match "ogr 0.0.1", shell_output("#{bin}/ogr --version")
    assert_match "usage:", shell_output("#{bin}/ogr --help")

    repo = testpath/"repo"
    system "git", "init", "-b", "feature/formula", repo
    system "git", "-C", repo, "remote", "add", "origin", "git@github.com:VijitSingh97/ogr.git"
    assert_equal "https://github.com/VijitSingh97/ogr", shell_output("#{bin}/ogr --print #{repo}").strip
    assert_equal "https://github.com/VijitSingh97/ogr/tree/feature%2Fformula",
                 shell_output("#{bin}/ogr --print --branch #{repo}").strip
  end
end
