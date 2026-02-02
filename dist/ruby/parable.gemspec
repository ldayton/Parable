Gem::Specification.new do |s|
  s.name        = 'parable-parser'
  s.version     = '0.1.0'
  s.summary     = 'A bash parser that exactly matches bash\'s behavior'
  s.description = 'A bash parser that exactly matches bash\'s behavior, transpiled from the reference Python implementation.'
  s.authors     = ['Lily Dayton']
  s.license     = 'MIT'
  s.homepage    = 'https://github.com/ldayton/Parable'
  s.metadata    = {
    'source_code_uri' => 'https://github.com/ldayton/Parable',
    'bug_tracker_uri' => 'https://github.com/ldayton/Parable/issues'
  }
  s.files       = ['lib/parable.rb']
  s.require_paths = ['lib']
  s.required_ruby_version = '>= 3.0'
end
